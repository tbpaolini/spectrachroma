from uuid import uuid4

for i in range(33):
    my_uuid = uuid4()

ms_guid = "{" + str(my_uuid).upper() + "}\n"

with open("GUIDs.txt", "a") as file:
    file.write(ms_guid)