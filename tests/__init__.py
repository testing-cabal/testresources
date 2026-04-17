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


def test_suite():
    from . import (
        TestUtil,
        test_optimising_test_suite,
        test_resource_graph,
        test_resourced_test_case,
        test_test_loader,
        test_test_resource,
    )

    result = TestUtil.TestSuite()
    result.addTest(test_test_loader.test_suite())
    result.addTest(test_test_resource.test_suite())
    result.addTest(test_resourced_test_case.test_suite())
    result.addTest(test_resource_graph.test_suite())
    result.addTest(test_optimising_test_suite.test_suite())
    return result
