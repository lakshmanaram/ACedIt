import sys
import json
import re
import os
try:
    from bs4 import BeautifulSoup as bs
    import requests as rq
    import grequests as grq
    from argparse import ArgumentParser
except:
    err = """
    You haven't installed the required dependencies.
    Run 'python setup.py install' to install the dependencies.
    """
    print err
    sys.exit(0)


class Utilities:

    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "ACedIt")

    @staticmethod
    def parse_flags():
        """
        Utility function to parse command line flags
        """

        parser = ArgumentParser()

        parser.add_argument("-s", "--site",
                            dest="site",
                            help="The competitive programming platform, e.g. codeforces, codechef etc")

        parser.add_argument("-c", "--contest",
                            dest="contest",
                            help="The name of the contest, e.g. JUNE17, LTIME49, COOK83 etc")

        parser.add_argument("-p", "--problem",
                            dest="problem",
                            help="The problem code, e.g. OAK, PRMQ etc")

        parser.add_argument("-f", "--force",
                            dest="force",
                            action="store_true",
                            help="Force download the test cases, even if they are cached")

        parser.add_argument("-sub","--submission",
                            dest="submission",
                            help="The number of AC'd submissions")

        parser.add_argument("-status",
                            dest="status",
                            help="The submission status, e.g. AC, WA etc")

        parser.add_argument("-u","--username",
                            dest="username",
                            help="The username, e.g. rng_58, rajat1603 etc")

        parser.set_defaults(force=False)

        args = parser.parse_args()

        flags = {}

        if args.site is None:
            import json
            default_site = None
            try:
                with open("constants.json", "r") as f:
                    data = f.read()
                data = json.loads(data)
                default_site = data.get("default_site", None)
            except:
                pass

            flags["site"] = default_site
        else:
            flags["site"] = args.site

        flags["contest"] = args.contest
        flags["problem"] = args.problem
        flags["force"] = args.force
        flags["site"] = flags["site"].lower()
        flags["submission"] = args.submission
        flags["status"] = args.status
        flags["username"] = args.username

        return flags

    @staticmethod
    def check_cache(site, contest, problem):
        """
        Method to check if the test cases already exist in cache
        If not, create the directory structure to store test cases
        """
        if problem is None:
            if not os.path.isdir(os.path.join(Utilities.cache_dir, site, contest)):
                os.makedirs(os.path.join(Utilities.cache_dir, site,
                                         contest))
            return False

        if os.path.isdir(os.path.join(Utilities.cache_dir, site, contest, problem)):
            return True
        else:
            os.makedirs(os.path.join(Utilities.cache_dir, site,
                                     contest, problem))
            return False

    @staticmethod
    def store_files(site, contest, problem, inputs, outputs):
        """
        Method to store the test cases in files
        """
        for i, inp in enumerate(inputs):
            filename = os.path.join(
                Utilities.cache_dir, site, contest, problem, "Input" + str(i))
            with open(filename, "w") as handler:
                handler.write(inp)

        for i, out in enumerate(outputs):
            filename = os.path.join(
                Utilities.cache_dir, site, contest, problem, "Output" + str(i))
            with open(filename, "w") as handler:
                handler.write(out)

    @staticmethod
    def download_problem_testcases(args):
        if args["site"] == "codeforces":
            platform = Codeforces(args)
        elif args["site"] == "codechef":
            platform = Codechef(args)
        elif args["site"] == "spoj":
            platform = Spoj(args)
        else:
            platform = Hackerrank(args)

        is_in_cache = Utilities.check_cache(
            platform.site, platform.contest, platform.problem)

        if not args['force'] and is_in_cache:
            print "Test cases found in cache..."
            sys.exit(0)

        platform.scrape_problem()

    @staticmethod
    def download_contest_testcases(args):
        if args["site"] == "codeforces":
            platform = Codeforces(args)
        elif args["site"] == "codechef":
            platform = Codechef(args)
        elif args["site"] == "hackerrank":
            platform = Hackerrank(args)

        Utilities.check_cache(
            platform.site, platform.contest, platform.problem)

        platform.scrape_contest()

    @staticmethod
    def get_html(url):
        """
        Utility function get the html content of an url
        """
        try:
            r = rq.get(url)
        except Exception as e:
            print "Please check your internet connection and try again."
            sys.exit(0)
        return r


class Codeforces:
    """
    Class to handle downloading of test cases from Codeforces
    """

    def __init__(self, args):
        self.site = args["site"]
        self.contest = args["contest"]
        self.problem = args["problem"]
        self.force_download = args["force"]

    def parse_html(self, req):
        """
        Method to parse the html and get test cases
        from a codeforces problem
        """
        soup = bs(req.text, "html.parser")

        inputs = soup.findAll("div", {"class": "input"})
        outputs = soup.findAll("div", {"class": "output"})

        repls = ("<br>", "\n"), ("<br/>", "\n"), ("</br>", "")

        formatted_inputs, formatted_outputs = [], []

        for inp in inputs:
            pre = inp.find("pre").decode_contents()
            pre = reduce(lambda a, kv: a.replace(*kv), repls, pre)
            pre = re.sub('<[^<]+?>', '', pre)
            formatted_inputs += [pre]

        for out in outputs:
            pre = out.find("pre").decode_contents()
            pre = reduce(lambda a, kv: a.replace(*kv), repls, pre)
            pre = re.sub('<[^<]+?>', '', pre)
            formatted_outputs += [pre]

        print "Inputs", formatted_inputs
        print "Outputs", formatted_outputs

        return formatted_inputs, formatted_outputs

    def get_problem_links(self, req):
        """
        Method to get the links for the problems
        in a given codeforces contest
        """
        soup = bs(req.text, "html.parser")

        table = soup.find("table", {"class": "problems"})
        links = ["http://codeforces.com" +
                 td.find("a")["href"] for td in table.findAll("td", {"class": "id"})]

        return links

    def scrape_problem(self):
        """
        Method to scrape a single problem from codeforces
        """
        print "Fetching problem " + self.contest + "-" + self.problem + " from Codeforces..."
        url = "http://codeforces.com/contest/" + \
            self.contest + "/problem/" + self.problem
        req = Utilities.get_html(url)
        inputs, outputs = self.parse_html(req)
        Utilities.store_files(self.site, self.contest,
                              self.problem, inputs, outputs)

    def scrape_contest(self):
        """
        Method to scrape all problems from a given codeforces contest
        """
        print "Checking problems available for contest " + self.contest + "..."
        url = "http://codeforces.com/contest/" + self.contest
        req = Utilities.get_html(url)
        links = self.get_problem_links(req)

        print "Found problems"
        print "\n".join(links)

        if not self.force_download:
            cached_problems = os.listdir(os.path.join(
                Utilities.cache_dir, self.site, self.contest))
            links = [link for link in links if link.split(
                "/")[-1] not in cached_problems]

        rs = (grq.get(link) for link in links)
        responses = grq.map(rs)

        for response in responses:
            if response is not None and response.status_code == 200:
                inputs, outputs = self.parse_html(response)
                self.problem = response.url.split("/")[-1]
                Utilities.check_cache(self.site, self.contest, self.problem)
                Utilities.store_files(
                    self.site, self.contest, self.problem, inputs, outputs)


class Codechef:
    """
    Class to handle downloading of test cases from Codechef
    """

    def __init__(self, args):
        self.site = args["site"]
        self.contest = args["contest"]
        self.problem = args["problem"]
        self.force_download = args["force"]

    def parse_html(self, req):
        """
        Method to parse the html and get test cases
        from a codechef problem
        """
        data = json.loads(req.text)
        soup = bs(data["body"], "html.parser")

        test_cases = soup.findAll("pre")
        formatted_inputs, formatted_outputs = [], []

        input_list = [
            "<pre>(.|\n)*<b>Input:?</b>:?",
            "<b>Output:?</b>(.|\n)+</pre>"
        ]

        output_list = [
            "<pre>(.|\n)+<b>Output:?</b>:?",
            "</pre>"
        ]

        input_regex = re.compile("(%s)" % "|".join(input_list))
        output_regex = re.compile("(%s)" % "|".join(output_list))

        for case in test_cases:
            inp = input_regex.sub("", str(case))
            out = output_regex.sub("", str(case))

            inp = re.sub('<[^<]+?>', '', inp)
            out = re.sub('<[^<]+?>', '', out)

            formatted_inputs += [inp.strip()]
            formatted_outputs += [out.strip()]

        print "Inputs", formatted_inputs
        print "Outputs", formatted_outputs

        return formatted_inputs, formatted_outputs

    def get_problem_links(self, req):
        """
        Method to get the links for the problems
        in a given codechef contest
        """
        soup = bs(req.text, "html.parser")

        table = soup.find("table", {"class": "dataTable"})
        links = [div.find("a")["href"]
                 for div in table.findAll("div", {"class": "problemname"})]
        links = ["https://codechef.com/api/contests/" + self.contest +
                 "/problems/" + link.split("/")[-1] for link in links]

        return links

    def scrape_problem(self):
        """
        Method to scrape a single problem from codechef
        """
        print "Fetching problem " + self.contest + "-" + self.problem + " from Codechef..."
        url = "https://codechef.com/api/contests/" + \
            self.contest + "/problems/" + self.problem
        req = Utilities.get_html(url)
        inputs, outputs = self.parse_html(req)
        Utilities.store_files(self.site, self.contest,
                              self.problem, inputs, outputs)

    def scrape_contest(self):
        """
        Method to scrape all problems from a given codechef contest
        """
        print "Checking problems available for contest " + self.contest + "..."
        url = "https://codechef.com/" + self.contest
        req = Utilities.get_html(url)
        links = self.get_problem_links(req)

        print "Found problems"
        print "\n".join(links)

        if not self.force_download:
            cached_problems = os.listdir(os.path.join(
                Utilities.cache_dir, self.site, self.contest))
            links = [link for link in links if link.split(
                "/")[-1] not in cached_problems]

        rs = (grq.get(link) for link in links)
        responses = grq.map(rs)

        print responses

        for response in responses:
            if response is not None and response.status_code == 200:
                inputs, outputs = self.parse_html(response)
                self.problem = response.url.split("/")[-1]
                Utilities.check_cache(self.site, self.contest, self.problem)
                Utilities.store_files(
                    self.site, self.contest, self.problem, inputs, outputs)


class Spoj:
    """
    Class to handle downloading of test cases from Spoj
    """

    def __init__(self, args):
        self.site = args["site"]
        self.contest = args["contest"]
        self.problem = args["problem"]
        self.force_download = args["force"]

    def parse_html(self, req):
        """
        Method to parse the html and get test cases
        from a spoj problem
        """
        soup = bs(req.text, "html.parser")

        test_cases = soup.findAll("pre")
        formatted_inputs, formatted_outputs = [], []

        input_list = [
            "<pre>(.|\n|\r)*<b>Input:?</b>:?",
            "<b>Output:?</b>(.|\n|\r)*"
        ]

        output_list = [
            "<pre>(.|\n|\r)*<b>Output:?</b>:?",
            "</pre>"
        ]

        input_regex = re.compile("(%s)" % "|".join(input_list))
        output_regex = re.compile("(%s)" % "|".join(output_list))

        for case in test_cases:
            inp = input_regex.sub("", str(case))
            out = output_regex.sub("", str(case))

            inp = re.sub('<[^<]+?>', '', inp)
            out = re.sub('<[^<]+?>', '', out)

            formatted_inputs += [inp.strip()]
            formatted_outputs += [out.strip()]

        print "Inputs", formatted_inputs
        print "Outputs", formatted_outputs

        return formatted_inputs, formatted_outputs

    def scrape_problem(self):
        """
        Method to scrape a single problem from spoj
        """
        print "Fetching problem " + self.problem + " from SPOJ..."
        url = "http://spoj.com/problems/" + self.problem
        req = Utilities.get_html(url)
        inputs, outputs = self.parse_html(req)
        Utilities.store_files(self.site, self.contest,
                              self.problem, inputs, outputs)


class Hackerrank:
    """
    Class to handle downloading of test cases from Hackerrank
    """

    def __init__(self, args):
        self.site = args["site"]
        self.contest = args["contest"]
        self.problem = "-".join(args["problem"].split()).lower()
        self.force_download = args["force"]

    def parse_html(self, req):
        """
        Method to parse the html and get test cases
        from a hackerrank problem
        """
        data = json.loads(req.text)
        soup = bs(data["model"]["body_html"], "html.parser")

        input_divs = soup.findAll("div", {"class": "challenge_sample_input"})
        output_divs = soup.findAll("div", {"class": "challenge_sample_output"})

        inputs = [input_div.find("pre") for input_div in input_divs]
        outputs = [output_div.find("pre") for output_div in output_divs]

        regex_list = [
            "<pre>(<code>)?",
            "(</code>)?</pre>"
        ]

        regex = re.compile("(%s)" % "|".join(regex_list))

        formatted_inputs, formatted_outputs = [], []

        for inp in inputs:
            spans = inp.findAll("span")
            if len(spans) > 0:
                formatted_input = "\n".join(
                    [span.decode_contents() for span in spans])
            else:
                formatted_input = regex.sub("", str(inp))

            formatted_inputs += [formatted_input.strip()]

        for out in outputs:
            spans = out.findAll("span")
            if len(spans) > 0:
                formatted_output = "\n".join(
                    [span.decode_contents() for span in spans])
            else:
                formatted_output = regex.sub("", str(out))

            formatted_outputs += [formatted_output.strip()]

        print "Inputs", formatted_inputs
        print "Outputs", formatted_outputs

        return formatted_inputs, formatted_outputs

    def scrape_problem(self):
        """
        Method to scrape a single problem from hackerrank
        """
        print "Fetching problem " + self.contest + "-" + self.problem + " from Hackerrank..."
        url = "https://www.hackerrank.com/rest/contests/" + \
            self.contest + "/challenges/" + self.problem
        req = Utilities.get_html(url)
        inputs, outputs = self.parse_html(req)
        Utilities.store_files(self.site, self.contest,
                              self.problem, inputs, outputs)
