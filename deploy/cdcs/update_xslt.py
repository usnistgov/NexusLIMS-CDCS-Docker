import os as _os
import requests as _requests
from glob import glob as _glob
from urllib.parse import urljoin as _urljoin
import warnings as _warnings
from urllib3.exceptions import InsecureRequestWarning as _InsecReqWarning
import logging as _logging
import argparse

logger = _logging.getLogger()
_warnings.filterwarnings("ignore",
                         category=_InsecReqWarning)


def get_current_xslt_ids(names):
    """
    Get the id values of XSLT resources on the server

    Parameters
    ----------
    names : list of str
        The names of the stylesheets to update (i.e. usually `"detail"` and
        `"list"`)

    Returns
    -------
    xslt_ids : dict
        a dictionary of the XSLT id values, with the values in `names` as
        keys and the ID values as values
    """
    headers = {'Content-Type': "application/json",
               'Accept': 'application/json', }
    url = _urljoin(_cdcs_url, f'rest/xslt/')
    xslt_ids = {}
    resp = _requests.request("GET", url, headers=headers,
                             auth=(username, password), verify=False)

    if resp.status_code == 200:
        for xsl in resp.json():
            # xsl is a dictionary with each response
            if xsl['name'] not in names:
                # ignore any XSL documents that don't have one of the
                # specified names
                continue
            else:
                xslt_ids[xsl['name']] = xsl['id']
        return xslt_ids
    else:
        raise ConnectionError(f'Could not parse response from {url}; '
                              f'Response text was: {resp.text}')


def replace_xslt_files(detail, list):
    if detail is None and list is None:
        print('ERROR: One of either "--detail" or "--list" must be specified')
        return

    list_xsl_file = list
    detail_xsl_file = detail

    print(f'Using {list} and {detail}\n')
    
    names_to_update = []
    
    if list is not None:
        with open(list) as f:
            list_content = f.read()
        names_to_update.append("list.xsl")
    if detail is not None:
        with open(detail_xsl_file) as f:
            detail_content = f.read()
        names_to_update.append("detail.xsl")

    xslt_ids = get_current_xslt_ids(names_to_update)

    headers = {'Content-Type': "application/json",
               'Accept': 'application/json'}

    print(xslt_ids)

    if list is not None:
        list_payload = {"id": xslt_ids['list.xsl'],
                        "name": "list.xsl",  # name of XSL
                        "filename": "list.xsl",  # filename of XSL
                        "content": list_content,  # xml content of XSL
                        "_cls": "XslTransformation"}
        list_xsl_endpoint = _urljoin(_cdcs_url, 
                                     f'rest/xslt/{xslt_ids["list.xsl"]}/')
        list_response = _requests.request("PATCH", list_xsl_endpoint,
                                          json=list_payload, headers=headers,
                                          auth=(username, password), 
                                          verify=False)
        print(f"List XSL: {list_xsl_endpoint}\n", list_response.status_code)

    if detail is not None:
        detail_payload = {"id": xslt_ids['detail.xsl'],
                        "name": "detail.xsl",  # name of XSL
                        "filename": "detail.xsl",  # filename of XSL
                        "content": detail_content,  # xml content of XSL
                        "_cls": "XslTransformation"}
        detail_xsl_endpoint = _urljoin(_cdcs_url,
                                       f'rest/xslt/{xslt_ids["detail.xsl"]}/')
        detail_response = _requests.request("PATCH", detail_xsl_endpoint,
                                            json=detail_payload, headers=headers,
                                            auth=(username, password), verify=False)
        print(f"\nDetail XSL: {detail_xsl_endpoint}\n", detail_response.status_code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Upload XSLs to a CDCS instance')
    parser.add_argument('--url',
                        help='Full URL of the CDCS instance')
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--detail', 
                        help="Path to the \"detail\" XSLT to be replaced",
                        default=None)
    parser.add_argument('--list',
                        help="Path to the \"list\" XSLT to be replaced",
                        default=None)

    args = parser.parse_args()

    username = args.username
    password = args.password
    _cdcs_url = args.url

    replace_xslt_files(args.detail, args.list)
