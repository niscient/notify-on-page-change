# notify-on-page-change

## Description
Allows you to specify a bunch of URLs you want to monitor for changes. Email alerts are sent when the contents of any of these pages changes.

Changes are detected purely based on a textual representation of the page contents. **Visual, screenshot-based changes are not currently supported**. For example, if a page changes the use of a character `a` to `b`, that change will be detected. But if they change the image used in an `<img>` tag, that won't be detected.

### Similar programs
There aren't many other programs which do page change monitoring, although there are many web services which charge a monthly fee. There is an Android app (WWW Notifier Pro) which notifies you when pages change, but iOS limitations prevent this sort of automatic checking. Distill is a Chrome extension which can do page change monitoring, but requires you to make an account and use Distill's servers to send email reminders. Note that some sites deliberately block access attempts from servers known to be used by page monitoring services.

## Usage

### Setting up
You need to specify the email address of the person who will receive emails. In order to send emails, you need to have login credentials for an account on some SMTP server (such as Gmail's servers). Note that, if you are using a Gmail account to send emails, you must allow less secure apps to access the account: https://myaccount.google.com/lesssecureapps

Sample `settings.ini` file:

```
[Program]
notify_email_address=my_personal_email@emailhost.com

[Email Server]
email_address=another_email@emailhost.com
password=plaintext_password
smtp_server=smtp.gmail.com
port=465

[Example1]
url=https://somesite.com/page1.html
check_every_x_hours=6

[Example2]
url=https://somesite.com/page2.html
check_every_x_hours=6
```

As you can see, you have to provide the plaintext password use to log into the account you're using to send emails. (Note that popular browsers such as Chrome store passwords in visible plaintext as well.)

Note that you can set how often each individual page is checked to see if its contents have changed.

### Running program

Once you have your config file, install the Python library dependencies (Requests and Beautiful Soup 4) and run the program in Python 3. Assuming `pip` and `python` are your Python 3 pip and python executables, you would run:
```
pip install requests
pip install beautifulsoup4
python notify_on_page_change.py
```

Abort the program by pressing Ctrl+C to stop monitoring for web page changes.

## Future improvements

* Allow checks to be run every X minutes instead of every X hours
* Allow user to input email server password manually every time program is run
* Create Windows executable

### Unlikely to be added anytime soon
* Visual (screenshot-based) partial-page comparisons. Unlikely to be added because:
    * This requires a GUI component (drag and drop to select relevant screen region)
    * Modern, non-PhantomJS Selenium web drivers only support taking screenshots of the first page rendered
* Support for sending login credentials. Unlikely to be added because:
    * The user would also have to specify form keys+values to be entered, and possibly HTTP request headers

If you really want some of these features, request them!
