import os
import random

URL = "172.27.0.50:5000/api/users"
URL = ":5000/api/users"
REMOTE_URL = "ec2-52-28-68-232.eu-central-1.compute.amazonaws.com"

male_names = ["Sebastian Stephan", "Michael Wirth", "Fabian Brun", "Robert Erdin", "Raphael Stanger","Fabio Schmid","Roman Ahrendt","Pascal Heid","David Sacher","Nikolaus Strassmann","Alessandro Buechel","Detlef Degen","Justin Hinrichs","Roman Feilhaber","Tilman Kornhaus"]
female_names = ["Rachel Gaertner","Sabine Rademacher","Leandra Cossmann","Corinne Rathenau","Nadine Gasser","Sophie Friedemann","Yvonne Frosch","Marlen Feulner","Isabell Kuttner","Michele Aach","Tanja Steitz","Juliane Scherrer","Tamara Felgenhauer","Patricia Storl"]

random.shuffle(male_names)
random.shuffle(female_names)

f=0
m=0
for fn in os.listdir('.'):
    if os.path.isfile(fn):
        if not fn.endswith('.py'):
            gender = fn.split('_')[0]
            id = fn.split('_')[1].split('.')[0]
            if gender == "male":
                id = id + "0" 
                name=male_names[m]
                m = m + 1
            else:
                name=female_names[f]
                f = f + 1

            command = (     "http -v " + URL + " " + \
                            "userid=1 "
                            "id=" + id + " " + \
                            "name='"+ name + "' " + \
                            "profilePic=http://" + REMOTE_URL + "/people/" + fn + " " + \
                            "age=" + str(random.randint(19,34)) + " " + \
                            "gender=" + gender + " ")
            os.system(command)
