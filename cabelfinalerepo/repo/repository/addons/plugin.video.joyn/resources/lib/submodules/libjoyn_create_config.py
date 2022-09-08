# -*- coding: utf-8 -*-

from xbmc import getCondVisibility
from sys import exit
from copy import deepcopy
from base64 import b64decode
from re import findall, search, sub
from json import loads
from collections import OrderedDict
from ..const import CONST
from ..xbmc_helper import xbmc_helper
from .. import compat
from .. import cache
from .. import request_helper

if compat.PY2:
	from urlparse import urlparse, urljoin
elif compat.PY3:
	from urllib.parse import urlparse, urljoin


def create_config(cached_config, addon_version):
	xbmc_helper().log_debug('get_config(): create config')
	use_outdated_cached_config = False

	config = {
	        'IS_ANDROID': False,
	        'IS_ARM': False,
	        'ADDON_VERSION': addon_version,
	        'country': None,
	        'http_headers': [],
	}

	# Fails on some systems
	try:
		os_uname = compat._uname_list()
	except Exception:
		os_uname = ['Linux', 'hostname', 'kernel-ver', 'kernel-sub-ver', 'x86_64']

	# android
	user_agent_suffix = 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36'
	if getCondVisibility('System.Platform.Android'):
		config['USER_AGENT'] = compat._format('Mozilla/5.0 (Linux; Android {}; {}) {}',
		        xbmc_helper().get_android_prop('ro.build.version.release', True) or '12',
		        xbmc_helper().get_android_prop('ro.product.model', True) or 'Pixel 6',
		        user_agent_suffix)
		config['IS_ANDROID'] = True

	# linux on arm uses widevine from chromeos
	elif os_uname[0] == 'Linux' and os_uname[4].lower().find('arm') != -1:
		config['USER_AGENT'] = compat._format('Mozilla/5.0 (X11; CrOS {} 14268.67.0) {}', os_uname[4], user_agent_suffix)
		config['IS_ARM'] = True
	elif os_uname[0] == 'Linux':
		config['USER_AGENT'] = compat._format('Mozilla/5.0 (X11; Linux {}) {}', os_uname[4], user_agent_suffix)
	elif os_uname[0] == 'Darwin':
		config['USER_AGENT'] = compat._format('Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) {}', user_agent_suffix)
	else:
		config['USER_AGENT'] = compat._format('Mozilla/5.0 (Windows NT 10.0; Win64; x64) {}', user_agent_suffix)

	html_content = request_helper.get_url(CONST['BASE_URL'], config)
	if html_content is None or html_content == '':
		xbmc_helper().notification(compat._format(xbmc_helper().translation('ERROR'), 'Url access'),
		                           compat._format(xbmc_helper().translation('MSG_NO_ACCESS_TO_URL'), CONST['BASE_URL']))
		exit(0)

	county_setting = xbmc_helper().get_setting('country')
	xbmc_helper().log_debug('COUNTRY SETTING: {}', county_setting)
	try:
		ip_api_response = request_helper.get_json_response(url=compat._format(CONST['IP_API_URL'],
		                                                                      xbmc_helper().translation('LANG_CODE')),
		                                                   config=config,
		                                                   silent=True)

	except Exception as e:
		xbmc_helper().log_debug('ip-api request failed - {}', e)
		ip_api_response = {
		        'status': 'success',
		        'country': 'Deutschland',
		        'countryCode': 'DE',
		}

	config.update({'actual_country': ip_api_response.get('countryCode', 'DE')})

	if county_setting == '' or county_setting == '0':
		xbmc_helper().log_debug('IP API Response is: {}', ip_api_response)
		if config.get('actual_country', 'DE') in CONST['COUNTRIES'].keys():
			config.update({'country': config.get('actual_country', 'DE')})
		else:
			xbmc_helper().dialog_action(
			        compat._format(xbmc_helper().translation('MSG_COUNTRY_INVALID'), ip_api_response.get('country', 'DE')))
			exit(0)
	else:
		for supported_country_key, supported_country in CONST['COUNTRIES'].items():
			if supported_country['setting_id'] == county_setting:
				config.update({'country': supported_country_key})
				break

	if config['country'] is None:
		xbmc_helper().dialog_action(xbmc_helper().translation('MSG_COUNTRY_NOT_DETECTED'))
		exit(0)

	do_break = False
	found_configs = 0
	parsed_preload_js_url = None
	preload_scripts = list(reversed(findall('<script.*?src="(.*?\.js)"', html_content)))
	for preload_js_url in preload_scripts:
		try:
			if not preload_js_url.startswith('http'):
				preload_js_url = urljoin(CONST['BASE_URL'], preload_js_url)
			if parsed_preload_js_url is None:
				parsed_preload_js_url = urlparse(preload_js_url)
			preload_js = request_helper.get_url(preload_js_url, config)
			for config_key, config_regex in CONST.get('PRELOAD_JS_CONFIGS').items():
				matches = findall(config_regex, preload_js)
				if len(matches) == 1:
					config[config_key] = matches[0]
					found_configs += 1
					if found_configs == len(CONST.get('PRELOAD_JS_CONFIGS')):
						do_break = True
						break
		except Exception as e:
			xbmc_helper().log_notice('Failed to load url: {} with exception {}', preload_js_url, e)
			pass

		if do_break:
			break

	if found_configs < len(CONST.get('PRELOAD_JS_CONFIGS')):
		use_outdated_cached_config = True

	if use_outdated_cached_config is False:
		found_configs = 0
		do_break = False
		for preload_js_url in preload_scripts:
			if preload_js_url.find('webpack') != -1:
				if not preload_js_url.startswith('http'):
					preload_js_url = urljoin(CONST['BASE_URL'], preload_js_url)

				webpack_json = []
				webpack_js = request_helper.get_url(preload_js_url, config)

				webpack_matches = findall('([0-9]+)-([^"]+).js', webpack_js)
				if webpack_matches:
					chunks = dict()
					for webpack_match in webpack_matches:
						chunks.update({webpack_match[0]: webpack_match[1]})
					webpack_json.append(dict(sep='-', items=chunks))

				webpack_matches = search('\+\"\.\"\+(.*?})', webpack_js)
				if webpack_matches:
					webpack_json.append(dict(sep='.', items=loads(sub(r'([0-9]+):("[^"]+"[,\n}])', r'"\1":\2', webpack_matches.group(1)))))

				for entry in webpack_json:
					for key, value in entry.get('items').items():
						try:
							chunks_src = compat._format('{}/{}{}{}.js', preload_js_url.rsplit('/', 1)[0], key, entry.get('sep') , value)
							chunks_js = request_helper.get_url(chunks_src, config)

							if not 'entitlementBaseUrl' in config:
								entitlementBaseUrl = search('entitlementBaseUrl.*?"([^"]*)', chunks_js)
								if entitlementBaseUrl and entitlementBaseUrl.group(1).startswith('http'):
									config['entitlementBaseUrl'] = entitlementBaseUrl.group(1)
									found_configs += 1

							if not 'playbackApiBaseUrl' in config:
								playbackApiBaseUrl = search('playbackApiBaseUrl.*?"([^"]*)', chunks_js)
								if playbackApiBaseUrl and playbackApiBaseUrl.group(1).startswith('http'):
									config['playbackApiBaseUrl'] = playbackApiBaseUrl.group(1)
									found_configs += 1

							if 'entitlementBaseUrl' in config and 'playbackApiBaseUrl' in config:
								do_break = True
						except Exception as e:
							xbmc_helper().log_notice('Failed to load url: {} with exception {}', chunks_src, e)
							pass
						if do_break:
							break
					if do_break:
						break

			elif preload_js_url.find('_buildManifest') != -1:
				if not preload_js_url.startswith('http'):
					preload_js_url = urljoin(CONST['BASE_URL'], preload_js_url)
				if parsed_preload_js_url is None:
					parsed_preload_js_url = urlparse(preload_js_url)

				manifest_js = request_helper.get_url(preload_js_url, config)
				manifest_matches = list(reversed(findall('(static\/chunks\/\d{3,4}-.*?.js)', manifest_js)))

				for manifest_match in manifest_matches:
					try:
						chunks_src = compat._format('{}/{}', preload_js_url.rsplit('/', 3)[0], manifest_match)
						chunks_js = request_helper.get_url(chunks_src, config)

						if not 'entitlementBaseUrl' in config:
							entitlementBaseUrl = search('entitlementBaseUrl.*?"([^"]*)', chunks_js)
							if entitlementBaseUrl and entitlementBaseUrl.group(1).startswith('http'):
								config['entitlementBaseUrl'] = entitlementBaseUrl.group(1)
								found_configs += 1

						if not 'playbackApiBaseUrl' in config:
							playbackApiBaseUrl = search('playbackApiBaseUrl.*?"([^"]*)', chunks_js)
							if playbackApiBaseUrl and playbackApiBaseUrl.group(1).startswith('http'):
								config['playbackApiBaseUrl'] = playbackApiBaseUrl.group(1)
								found_configs += 1

						if 'entitlementBaseUrl' in config and 'playbackApiBaseUrl' in config:
							do_break = True
					except Exception as e:
						xbmc_helper().log_notice('Failed to load url: {} with exception {}', chunks_src, e)
						pass
					if do_break:
						break
			if do_break:
				break

		if found_configs != 2:
			use_outdated_cached_config = True

	if use_outdated_cached_config is False:
		config['GRAPHQL_HEADERS'] = [('x-api-key', config['API_GW_API_KEY']),
		                             ('Joyn-Platform', xbmc_helper().get_text_setting('joyn_platform'))]

	config['CLIENT_NAME'] = xbmc_helper().get_text_setting('joyn_platform')

	if use_outdated_cached_config is True:
		if cached_config is not None and isinstance(cached_config, dict):
			xbmc_helper().log_notice('!!!Using outdated cached config - from addon version {} !!!',
			                         cached_config.get('ADDON_VERSION', '[UNKNOWN]'))
			_config = deepcopy(cached_config)
			_config.update({
			        'IS_ANDROID': config.get('IS_ANDROID', cached_config.get('IS_ANDROID', False)),
			        'IS_ARM': config.get('IS_ARM', cached_config.get('IS_ARM', False)),
			        'actual_country': config.get('actual_country', cached_config.get('actual_country', '')),
			        'country': config.get('country', cached_config.get('country', 'DE')),
			        'USER_AGENT': config.get('USER_AGENT', cached_config.get('USER_AGENT', '')),
			})
			config = _config
		else:
			xbmc_helper().log_error('Configuration could not be extracted and no valid cached config exists. Giving Up!')
			xbmc_helper().notification(compat._format(xbmc_helper().translation('ERROR'), ''),
			                           compat._format(xbmc_helper().translation('MSG_CONFIG_VALUES_INCOMPLETE'), ''))
			exit(0)
	else:
		cache.set_json('CONFIG', config)

	return config
