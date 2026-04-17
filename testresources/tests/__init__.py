#  testresources: extensions to python unittest to allow declaritive use
#  of resources by test cases.
#
#  Copyright (c) 2005-2010 Testresources Contributors
#
#  Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
#  license at the users choice. A copy of both licenses are available in the
#  project source as Apache-2.0 and BSD. You may not use this file except in
#  compliance with one of these two licences.
#
#  Unless required by applicable law or agreed to in writing, software distributed
#  under these licenses is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#  CONDITIONS OF ANY KIND, either express or implied.  See the license you chose
#  for the specific language governing permissions and limitations under that
#  license.

from unittest import TestResult


class ResultWithoutResourceExtensions:
    """A test fake which does not have resource extensions."""


class ResultWithResourceExtensions(TestResult):
    """A test fake which has resource extensions."""

    def __init__(self):
        TestResult.__init__(self)
        self._calls = []

    def startCleanResource(self, resource):
        self._calls.append(("clean", "start", resource))

    def stopCleanResource(self, resource):
        self._calls.append(("clean", "stop", resource))

    def startMakeResource(self, resource):
        self._calls.append(("make", "start", resource))

    def stopMakeResource(self, resource):
        self._calls.append(("make", "stop", resource))

    def startResetResource(self, resource):
        self._calls.append(("reset", "start", resource))

    def stopResetResource(self, resource):
        self._calls.append(("reset", "stop", resource))
