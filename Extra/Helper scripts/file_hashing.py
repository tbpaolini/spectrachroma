from hashlib import sha1

file = open(r"C:\Users\Tiago\OneDrive\Documentos\Python\Projetos\CIE Chromaticity\lib\About.txt", "r")
file.readline()
check1 = sha1(bytes(file.readline(), "utf-8"))
check2 = sha1(bytes(file.readline(), "utf-8"))
file.close()

print(check1.hexdigest())
print(check2.hexdigest())