import requests
import re
import sys
import getopt
from joblib import Parallel, delayed

# Globals
targetURL = ""
targetMode = "HEAD"
targetFilterDomain = ""
targetFilterExtension = []
verbose = False

def parseArgs(argv):

    global targetURL, targetMode, targetFilterDomain, targetFilterExtension, verbose
    
    try:
        opts, args = getopt.getopt(argv,"", ["url=", "mode=", "filter-domain=", "filter-extension=", "verbose"])
    except getopt.GetoptError:
        print("link-checker.py --url=\"<URL>\" --mode=<HEAD|GET> --filter-domain=<DOMAIN> --filter-extension=\"<jpg,png>\"")
        sys.exit(1)
    
    for opt, arg in opts:
        if opt == '--help':
            print("link-checker.py --url=\"<URL>\" --mode=<HEAD|GET> --filter-domain=\"<DOMAIN>\" --filter-extension=\"<jpg,png>\"")
            sys.exit(1)
        elif opt == "--url":
            targetURL = arg
        elif opt == "--mode":
            targetMode = arg
        elif opt == "--filter-domain":
            targetFilterDomain = arg
        elif opt == "--filter-extension":
            targetFilterExtension = arg.split(",")
        elif opt == "--verbose":
            verbose = True

    if len(targetURL)<1:
        print("link-checker.py --url=\"<URL>\" --mode=<HEAD|GET> --filter-domain=<DOMAIN> --filter-extension=\"<jpg,png>\"")
        sys.exit(1)
    
    print("### LINK-CHECKER ###")
    print("URL: ", targetURL)
    print("Mode: ",targetMode)
    print("Filter domain: ",targetFilterDomain)
    print("Filter extension: ",targetFilterExtension)

    begin()

def checkURL(in_url):
    if targetMode == "GET":
        response = requests.get(in_url)
    else:
        response = requests.head(in_url)
    if response.status_code == 200:
        print("Result: OK - " + in_url)
    else:
        exitCode = 1
        print("Result: NOK - " + in_url + " STATUS: " +  str(response.status_code))
        return in_url

def begin():

    # Load target URL
    r = requests.get(targetURL)

    if verbose:
        print("RESPONSE", r.text)

    # Response ok ?
    if r.status_code != 200:
        print("\nError: incorrect response code from target URL!")
        sys.exit(0)

    # Domain filter ?
    if len(targetFilterDomain) > 0:
        pattern = re.compile(rf"(https?:\/\/{re.escape(targetFilterDomain)}.*?)[\'|\"|\s]", re.MULTILINE|re.UNICODE)
    else:
        pattern = re.compile(r"(https?:\/\/.*?)[\'|\"|\s]", re.MULTILINE|re.UNICODE)

    # Build match list
    matchList = set()
    for m in re.finditer(pattern, r.text):
        if len(targetFilterExtension)>0:
            for ext in targetFilterExtension:
                if m.group(1)[-(len(ext)):] == ext:
                    matchList.add(m.group(1))
        else:
            matchList.add(m.group(1))

    if verbose:
        print("URL LIST:", matchList)

    # No matches found
    if len(matchList)==0:
        print("\nNo URL:s found!")
        sys.exit(0)

    print("\nURLs found: ", len(matchList))

    # Check URLs in match list in parallel
    results = Parallel(n_jobs=-1)(delayed(checkURL)(url) for url in matchList)

    # Check results
    errList = set()
    for result in results:
        if not result is None:
            errList.add(result)

    # Errors found ?
    if len(errList) > 0:
        print("\nErrors found!")
        sys.exit(1)
    else:
        print("\nNo errors found!")
        sys.exit(0)

if __name__ == "__main__":
    parseArgs(sys.argv[1:])