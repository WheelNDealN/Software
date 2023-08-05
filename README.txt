                   ----Overview----
This application is an inventory management project.
an example use of this is if a employee wants a new piece of hardware
they must login, and create a new request.

                  ----How to create a user/navigate----
the login is fairly straight forward and create a user creates a user.
for the two factor authentification you must create a user
then add the secret code to the google app on your Phone
and type in the time limited code that pops up this will sign you in.
However its important to know if you dont set up 2fa correctly
you are unable to get the code again. Idealy i was going
to implement an email service however i found out they are all 
ubscription based and they cost alot of money so decided its best to
have it displayed once. to modify or change anything it all runs of the
id you provide, its next to whatever you need to change, simply type the
number then press an assosiated button that you want to complete.

                    ----Admin acocunt----
An admin account can be made by using the password "pa$$word",
this isnt how it should be done in a real application, however for
ease of testing for the marker its a simple specific password.
i am able to make anyone an admin through the database,
however to be able to set up 2fa the admin needs to be created
to recieve the 2fa code for the app.

                    ----IMPORTANT----
PRESS BUTTONS RATHER THAN PRESSING ENTER ON THE KEYBOARD
after testing with a friend i learned if you press enter to natvigate,
it presses the first button available, which isnt always the option you want.
to mitigate this please just press buttons you want to use.
