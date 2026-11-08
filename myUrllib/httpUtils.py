# -*- coding: utf8 -*-
import json
import socket
from collections import OrderedDict
from time import sleep
import requests
import TickerConfig
from agency.agency_tools import proxy
from config import logger


def _set_header_default():
    header_dict = OrderedDict()
    # header_dict["Accept"] = "application/json, text/plain, */*"
    header_dict["Accept-Encoding"] = "gzip, deflate"
    header_dict[
        "User-Agent"] = _set_user_agent()
    header_dict["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    header_dict["Origin"] = "https://kyfw.12306.cn"
    header_dict["Connection"] = "keep-alive"
    return header_dict


def _set_user_agent():
    # Use Requests' transparent default UA; avoid a runtime lookup to a third-party
    # user-agent service during application startup.
    return requests.utils.default_user_agent()


def _redact_request_data(data):
    """Avoid writing credentials and authentication tokens to application logs."""
    sensitive_markers = ("password", "passwd", "pwd", "token", "secret",
                         "answer", "cookie", "authorization", "tk")
    if isinstance(data, dict):
        return {
            key: ("<redacted>" if any(marker in str(key).lower()
                                      for marker in sensitive_markers) else value)
            for key, value in data.items()
        }
    return "<redacted>" if data is not None else None


class HTTPClient(object):

    def __init__(self, is_proxy):
        """
        :param method:
        :param headers: Must be a dict. Such as headers={'Content_Type':'text/html'}
        """
        self.initS()
        self._cdn = None
        self._proxies = None
        if is_proxy == 1:
            self.proxy = proxy()
            self._proxies = self.proxy.setProxy()
            # print(u"设置当前代理ip为 {}, 请注意代理ip是否可用！！！！！请注意代理ip是否可用！！！！！请注意代理ip是否可用！！！！！".format(self._proxies))

    def initS(self):
        self._s = requests.Session()
        self._s.headers.update(_set_header_default())
        return self

    def set_cookies(self, kwargs):
        """
        设置cookies
        :param kwargs:
        :return:
        """
        for kwarg in kwargs:
            for k, v in kwarg.items():
                self._s.cookies.set(k, v)

    def get_cookies(self):
        """
        获取cookies
        :return:
        """
        return self._s.cookies.values()

    def del_cookies(self):
        """
        删除所有的key
        :return:
        """
        self._s.cookies.clear()

    def del_cookies_by_key(self, key):
        """
        删除指定key的session
        :return:
        """
        self._s.cookies.set(key, None)

    def setHeaders(self, headers):
        self._s.headers.update(headers)
        return self

    def resetHeaders(self):
        self._s.headers.clear()
        self._s.headers.update(_set_header_default())

    def getHeadersHost(self):
        return self._s.headers["Host"]

    def setHeadersHost(self, host):
        self._s.headers.update({"Host": host})
        return self

    def setHeadersUserAgent(self):
        self._s.headers.update({"User-Agent": _set_user_agent()})

    def getHeadersUserAgent(self):
        return self._s.headers["User-Agent"]

    def getHeadersReferer(self):
        return self._s.headers["Referer"]

    def setHeadersReferer(self, referer):
        self._s.headers.update({"Referer": referer})
        return self

    @property
    def cdn(self):
        return self._cdn

    @cdn.setter
    def cdn(self, cdn):
        self._cdn = cdn

    def send(self, urls, data=None, **kwargs):
        """send request to url.If response 200,return response, else return None."""
        allow_redirects = False
        is_logger = urls.get("is_logger", False)
        req_url = urls.get("req_url", "")
        re_try = urls.get("re_try", 0)
        s_time = urls.get("s_time", 0)
        is_cdn = urls.get("is_cdn", False)
        is_test_cdn = urls.get("is_test_cdn", False)
        error_data = {"code": 99999, "message": u"重试次数达到上限"}
        method = (urls.get("req_type") or ("post" if data is not None else "get")).lower()
        if method not in ("get", "post"):
            raise ValueError("Unsupported HTTP method: {}".format(method))
        self.resetHeaders()
        request_params = data if method == "get" else None
        request_data = data if method == "post" else None
        if urls.get("Referer"):
            self.setHeadersReferer(urls["Referer"])
        self.setHeadersUserAgent()
        if is_logger:
            logger.log(
                u"url: {0}\n入参: {1}\n请求方式: {2}\n".format(req_url, _redact_request_data(data), method, ))
        self.setHeadersHost(urls["Host"])
        if is_test_cdn:
            url_host = self._cdn
        elif is_cdn:
            if self._cdn:
                # print(u"当前请求cdn为{}".format(self._cdn))
                url_host = self._cdn
            else:
                url_host = urls["Host"]
        else:
            url_host = urls["Host"]
        http = urls.get("httpType") or "https"
        for i in range(re_try):
            try:
                # sleep(urls["s_time"]) if "s_time" in urls else sleep(0.001)
                sleep(s_time)
                response = self._s.request(method=method,
                                           timeout=2,
                                           proxies=self._proxies,
                                           url=http + "://" + url_host + req_url,
                                           data=request_data,
                                           params=request_params,
                                           allow_redirects=allow_redirects,
                                           verify=True,
                                           **kwargs)
                if response.status_code == 200 or response.status_code == 302:
                    if urls.get("not_decode", False):
                        return response.content
                    if response.content:
                        if is_logger:
                            logger.log(
                                u"响应状态：{0}，响应字节数：{1}".format(
                                    response.status_code, len(response.content)))
                        if urls["is_json"]:
                            return json.loads(response.content.decode() if isinstance(response.content, bytes) else response.content)
                        else:
                            return response.content.decode("utf8", "ignore") if isinstance(response.content, bytes) else response.content
                    else:
                        print(f"url: {urls['req_url']}返回参数为空, 接口状态码: {response.status_code}")
                        logger.log(
                            u"url: {} 返回参数为空".format(urls["req_url"]))
                        continue
                else:
                    sleep(urls["re_time"])
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                pass
            except socket.error:
                pass
        return error_data
