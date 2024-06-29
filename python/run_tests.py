"""Run tests"""
import sys
import argparse

from unittest import TextTestRunner

from tests import adminbot_suite, adminmgr_suite, pollbot_suite, pollmgr_suite

SUITES = {
    "adminbot": adminbot_suite,
    "adminmgr": adminmgr_suite,
    "pollbot": pollbot_suite,
    "pollmgr": pollmgr_suite,
}


def parse_all_args(args):
    p = argparse.ArgumentParser()

    p.add_argument(
        "suitenames",
        nargs="*",
        help="suites to run (choose from adminbot, adminmgr, pollbot, pollmgr)",
    )
    p.add_argument("-a", action="store_true", help="Run all tests")

    return p.parse_args(args)


def main(parsed_args):
    if parsed_args.a:
        suites = [adminbot_suite, adminmgr_suite, pollbot_suite, pollmgr_suite]
    else:
        suites = [SUITES[sname] for sname in parsed_args.suitenames]

    runner = TextTestRunner()
    for suite in suites:
        print(f"RUNNING SUITE {suite.__name__}")
        runner.run(suite())


if __name__ == "__main__":
    main(parse_all_args(sys.argv[1:]))
