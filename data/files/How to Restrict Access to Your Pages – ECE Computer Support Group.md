# How to Restrict Access to Your Pages

Web pages can be protected by placing a file named .htaccess in the web
directory. The ECE web server will detect this file and interpret its
instructions before allowing access to material in the directory (and its
subdirectories). The specific format of directives in the .htaccess file are
defined by the web server software from The Apache Group. Please be aware that
this restriction is done on a per-directory basis. If you have some files you
want open to the public, but some restricted, then you need to have two
separate directories.

Suppose you have a directory that you only want people on campus to be able to
see the contents. The following snipet of commands placed in a .htaccess file
in the directory /a/b/c/to/path would be used to implement that restriction.

    
    
    order deny,allow

    deny from all

    allow from .gatech.edu

There are other methods for restricting access, including the requirement of a
username/password combination.

You can password-protect your directories using the same single sign-on system
that is used by my.gatech.edu, T-Square, BuzzPort, and many other Georgia Tech
services. If you would like to restrict access to a directory so that anyone
with a Georgia Tech account can login, place the .htaccess file in the
directory to restrict and put the following in your file:

    
    
    AuthType Cas 

    Require valid-user

If, instead, you'd like to restrict access to a limited group of users, use
the following format in your .htaccess file, replacing "`_gb0 gburdell0_`"
with a space-separated list of Georgia Tech usernames for those who should be
able to login:

    
    
    AuthType Cas 

    Require user _gb0 gburdell0_

Please note that since this is a single sign-on service, if you are already
logged into another application that uses this service, you will not be asked
to login again. If you would rather be notified each time you are logging into
one of the single sign-on applications, make sure that you check the box next
to "Warn me before logging me into other sites" when you initially login to
the "Georgia Tech Login Service".

Note: The method that follows does not encrypt any of the transaction, so
usernames and passwords are sent in plain text. If you need a more secure
method of protecting your files, send an email to help@ece. We recommend that
you use NCSA-style user files which contain simple username: <enc passwd>
pairs. This advanced feature should only be used by experienced people. To do
so, you set up a .htaccess file very similar to above, but instead, you need
to add a database that contains the list of users you want to be able to
access the files. This database file consists of a list of username:password
pairs where the passwords are encrypted just like standard Unix passwords. In
order to reduce the complexity of managing these files, we have provided a
utility in /home/www/bin/userdb (accessible via ssh) that will allow you to
easily manage and maintain these NCSA style password files.

    
    
    usage: /home/www/bin/userdb -db _/path/to/your/password/file_ -action [username]

     

      -add username     Adds the specified user to the 

                        userdbfile, possibly creating 

                        the file.  Prompts for the 

                        user's password.

     

      -change username  Changes an existing user's 

                        password.

     

      -delete username  Removes the specified user 

                        from the userdbfile.

     

      -list             Displays the contents of the 

                        userdbfile.

     

      -help             Prints out information on how 

                        to use this program with 

                        Netscape server authentication.

    

To use an NCSA-style password file, you must refer to it in the .htaccess file
as shown:

    
    
    AuthUserFile _/path/to/your/password/file_

    AuthGroupFile /dev/null

    AuthName "_This is what the prompt will say_ "

    AuthType Basic

    require valid-user

    

Please note that references to your database files **MUST** include a fully
qualified pathname, and it must be world-readable. (Note: If your password
file is in a sub-directory of your users page, the
_/path/to/your/password/file_ will begin with "/home/www/users/" (for faculty
and staff) or "/home/webpages/" (for students) followed by your username and
the rest of the path to your password file. So, if I am faculty, and my
username is "abcd" and the sub-directory which contains my ".htpasswords" file
is called "private", then my AuthUserFile would be
"/home/www/users/abcd/private/.htpasswords" - without the quotes.) **NOTE:**
your password file should begin with .ht so that it cannot be read in a
browser.

**NOTE:** A lot of people think that they have access restrictions on their
pages, yet they unintentionally set the permissions on the files so that the
web server itself can not read them. In this case, the server returns an error
message pertaining to permissions, when it is really telling you the that the
file permissions are wrong. In order for the server to read your files, all
directories must be read-execute enabled to world, e.g. at least mode 755. All
files must at least be readable by the webserver, e.g. at least mode 644. You
can use the Unix `chmod` command to set these permissions properly.

Last revised January 5, 2016.

  * Contact the Institute
  * Directory

  * Offices
  * Campus Map
  * Apply
  * Support / Give

  * Log in

**Georgia Institute of Technology**  
North Avenue, Atlanta, GA 30332

404-894-2000

  * Emergency Information
  * Legal & Privacy Information
  * Human Trafficking Notice

  * Accessibility
  * Accountability
  * Accreditation
  * Employment

(C)2025 Georgia Institute of Technology

