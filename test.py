import hashlib 
password = "test"
salt = ("diD_h12$j")
password += salt
hashed = hashlib.md5(password.encode())  
hashed = hashed.hexdigest()
print(str(hashed))
