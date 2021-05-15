from app.models import Question, Like, Answer, Tag, Profile
from django.contrib.auth.models import User
from datetime import datetime

user = User.objects.create_user('aleksn7', password='qwerty12345')
user.is_superuser = False
user.is_staff = False
user.save()

user = User.objects.create_user('krushitelcherepov2009', password='qwerty12345')
user.is_superuser = False
user.is_staff = False
user.save()

Profile.objects.create(user=User.objects.get(username="aleksn7"))
Profile.objects.create(
    user=User.objects.get(username="krushitelcherepov2009"),
    avatar="/img/photo2.jpeg")

for i in range(10):
    Tag.objects.create(name=('tag'+str(i)))

for i in range(20):
    Question.objects.create(
        id=i,
        title='How to build a moon park?',
        text='Lorem ipsum dolor sit amet, consectetur \
            adipiscing elit, sed do eiusmod tempor incididunt \
            ut labore et dolore magna aliqua Ut enim ad minim \
            veniam, quis nostrud exercitation ullamco laboris \
            nisi ut aliquip ex ea commodo consequat. Duis aute \
            irure dolor in reprehenderit in voluptate velit esse \
            cillum dolore eu fugiat nulla pariatur. Excepteur \
            sint occaecat cupidatat non proident, sunt in culpa \
            qui officia deserunt mollit anim id est laborum.',
        author=User.objects.get(username="aleksn7"),
        is_active=True).tags.set(
            Tag.objects.filter(name=('tag' + str(i % 10 + 1))))


for i in range(20):
    Answer.objects.create(
        text="Example answer text",
        question=Question.objects.get(id=i),
        author=User.objects.get(username="krushitelcherepov2009"),
    )

for i in range(20):
    Like.objects.create(
        user=User.objects.get(username="krushitelcherepov2009"),
        content_object=Question.objects.get(id=i)
    )

for i in range(1, 21):
    Like.objects.create(
        user=User.objects.get(username="aleksn7"),
        content_object=Answer.objects.get(id=i)
    )
