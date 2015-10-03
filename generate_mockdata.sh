# rm test.db

http -v :5000/api/users \
name="Sebastian Stephan" \
profilePic="http://uziiw38pmyg1ai60732c4011.wpengine.netdna-cdn.com/wp-content/dropzone/2015/08/RTX1GZCO.jpg" \
age:=27 \
gender="male"

http -v :5000/api/users \
name="Leigh Richardson" \
profilePic="https://c2.staticflickr.com/4/3850/14995556677_568e490c5c.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="male"

http -v :5000/api/users \
name="Bradley Sherman" \
profilePic="http://i.telegraph.co.uk/multimedia/archive/02858/man_2858382b.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="male"

http -v :5000/api/users \
name="Joanne Frazier" \
profilePic="https://fs02.androidpit.info/a/ee/01/selfie-cam-vintage-edition-ee019f-h900.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="female"

http -v :5000/api/users \
name="Cory Fields" \
profilePic="http://blog.dictionary.com/wp-content/uploads/2013/11/selfie_big.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="female"

http -v :5000/api/users \
name="Annie	Moody" \
profilePic="http://thebridgehc.org/wp-content/uploads/2014/07/selfie.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="female"

http -v :5000/api/users \
name="Wade Stewart" \
profilePic="https://c1.staticflickr.com/3/2827/12149152535_793a1fbb50_b.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="male"

http -v :5000/api/users \
name="Norman Bowers" \
profilePic="https://s-media-cache-ak0.pinimg.com/736x/f0/48/a7/f048a78931a897bded2c4938b5e91e2a.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="male"

http -v :5000/api/users \
name="Beatrice	Mckenzie" \
profilePic="http://cdn2.ubergizmo.com/wp-content/uploads/2015/05/girl-selfie.jpg" \
age:=$(shuf -i 20-40 -n 1) \
gender="female"
