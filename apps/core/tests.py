from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

'''
class GPGTest(TestCase):
    verify = gpg.verify_file('/tmp/gpgtest/testfile.txt.gpg')
    gpg.sign_file('/tmp/gpgtest/testfile.txt', '/tmp/gpgtest/new')

    res = Resource('/tmp/gpgtest/image001.png')
    print res.uuid
    #print res.data

    cache = ContentCache('/tmp')
    cache.store(res)
'''
