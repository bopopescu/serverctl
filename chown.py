import sys
import os


def main(domain):
    homedir = '/var/www/hosts/' + domain

    res = False

    try:
        #os.mkdir(homedir)
        #os.chmod(homedir, 0o775)
        os.chown(homedir, 5500, 5500)
        #shutil.chown(homedir, user=5500, group=5500)

    except Exception as e:
        print(e)

if __name__ == '__main__':
    main(sys.argv[1])









