from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth import logout
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib.postgres.search import SearchVector, SearchRank, SearchQuery
import random
import urllib
import jwt
from cent import Client

from app.models import Question, Answer, Tag, Like, Profile
from app.forms import LoginForm, QuestionForm, RegisterForm, AnswerForm, SettingsForm
from askme.settings import DEFAULT_ITEMS_COUNT_ON_PAGE, MEDIA_ROOT, BASE_AVATAR, HMAC_TOKEN, API_TOKEN, CL, CACHE_INVALIDATE

def paginate(objects_list, page_number):
    pag = Paginator(objects_list, DEFAULT_ITEMS_COUNT_ON_PAGE)
    try:
        page_number = int(page_number)
    except TypeError:
        return pag.page(1).object_list, pag.page_range

    if page_number < 1:
        return pag.page(1).object_list, pag.page_range

    return pag.page(page_number).object_list, pag.page_range


def get_random_color():
    return "#%02X%02X%02X" % (
        random.randint(0, 255), 
        random.randint(0, 255),
        random.randint(0, 255),
    )


def get_top_tags():
    cache_value = cache.get("top_tags")
    if cache_value:
        return cache_value

    tags = [(
        {"name": i,
         "color": get_random_color(),
         "size": random.randint(17, 23)},
        Question.objects.filter(tags=i).count()
    ) for i in Tag.objects.all()]

    tags.sort(key=lambda x: x[1], reverse=True)
    tags = list(map(lambda x: x[0], tags[0:10]))
    cache.set("top_tags", tags, CACHE_INVALIDATE)

    return tags


def get_top_members():
    cache_value = cache.get("top_members")
    if cache_value:
        return cache_value

    members = [(i.username, Question.objects.filter(author=i).count() + Answer.objects.filter(author=i).count()) for i in DjangoUser.objects.all()]
    members.sort(key=lambda x: x[1], reverse=True)
    members = list(map(lambda x: x[0], members[0:5]))
    cache.set("top_members", members, CACHE_INVALIDATE)
    
    return members


def upload_image(file, user_id):
    with open(MEDIA_ROOT+f"/img/{user_id}", "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)

    return f"img/{user_id}"


def change_photos(user):
    for question in Question.objects.filter(author=user):
        question.save()
    for answer in Answer.objects.filter(author=user):
        answer.save()


# Create your views here.
def singup(request):
    if request.method == "GET":
        form = RegisterForm()
    else:
        form = RegisterForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            user = DjangoUser.objects.create_user(
                form.cleaned_data["username"],
                form.cleaned_data["email"],
                form.cleaned_data["password"])
            user.is_superuser = False
            user.is_staff = False
            user.save()
            if form.cleaned_data["avatar"]:
                image_path = upload_image(form.cleaned_data["avatar"], user.id)
            else:
                image_path = BASE_AVATAR

            Profile.objects.create(
                user=DjangoUser.objects.get(username=form.cleaned_data["username"]),
                avatar=image_path
            )
            return redirect("/login")

    return render(request, "singup.html", {
                "form": form,
           })


@login_required
def ask(request):
    if request.method == "GET":
        form = QuestionForm()
    else:
        form = QuestionForm(data=request.POST)
        if form.is_valid():
            tags = form.cleaned_data["tag"].split(" ")
            text = form.cleaned_data["text"]
            title = form.cleaned_data["title"]
            question = Question.objects.create(
                author=request.user, text=text, title=title
            )
            tags_list = list()
            for tag_name in tags:
                try:
                    tag = Tag.objects.get(name=tag_name)
                except Tag.DoesNotExist:
                    tag = Tag.objects.create(name=tag_name)
                tags_list.append(tag)
            question.tags.set(tags_list)
            question.save()
            return redirect(reverse("question", kwargs={"qid": question.pk}))

    return render(request, "ask.html", {
        "form": form,
    })


def index(request):
    questions_, paginates_range = paginate(
        Question.objects.all(), request.GET.get("page")
    )

    return render(request, "index.html", {
        "questions": questions_,
        "paginates": paginates_range,
    })


def login(request):
    if request.user.is_authenticated:
        redirect("/index")

    if request.method == "GET":
        form = LoginForm()
    else:
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = auth.authenticate(request, **form.cleaned_data)
            if user is not None:
                auth.login(request, user)
                next_ = request.GET.get("next")
                return redirect(f"{next_}")

    return render(request, "login.html", {
        "form": form,
        "previous": request.META.get("HTTP_REFERER"),
    })


def question(request, qid):
    question = get_object_or_404(Question, id=qid)
    if request.method == "GET":
        form = AnswerForm()
    else:
        form = AnswerForm(data=request.POST)
        if form.is_valid() and request.user.is_authenticated:
            answer = Answer.objects.create(
                text=form.cleaned_data["field"],
                author=request.user,
                question=question
            )

            CL.publish(f"question{question.id}", {
                    "answer": render_to_string("inc/answer.html", {
                        "answer": answer,
                    })
            })

    answers = Answer.objects.get_by_question(question)
    token = jwt.encode({"sub": "some_name"}, HMAC_TOKEN)
    return render(request, "question.html", {
        "form": form,
        "question": question,
        "answers": answers,
        "is_owner": (question.author == request.user),
        "TOKEN": token.decode(),
    })


def tag(request, tag):
    tag = get_object_or_404(Tag, name=urllib.parse.unquote(tag))
    questions_, paginates_range = paginate(
        Question.objects.get_by_tag(tag), request.GET.get("page"))
    return render(request, "tag.html", {
        "questions": questions_,
        "tag": tag,
        "paginates": paginates_range,
    })


@login_required
def logout_view(request):
    previous = request.META.get("HTTP_REFERER")
    logout(request)
    return redirect(previous)


@login_required
def settings(request):
    if request.method == "GET":
        form = SettingsForm(initial={
            "username": request.user.username,
            "email": request.user.email
        })
    else:
        form = SettingsForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            user = request.user
            if form.cleaned_data["username"] != user.username:
                user.username = form.cleaned_data["username"]
            if form.cleaned_data["email"] != user.email:
                user.email = form.cleaned_data["email"]
            if form.cleaned_data["password"]:
                user.set_password(form.cleaned_data["password"])
            if form.cleaned_data["avatar"]:
                profile = Profile.objects.get(user=user)
                new_photo = upload_image(form.cleaned_data["avatar"], user.id)
                flag = False
                if profile.avatar == BASE_AVATAR:
                    flag = True
                profile.avatar = new_photo
                profile.save()
                if flag:
                    change_photos(user)
            user.save()

    return render(request, "settings.html", {
        "form": form,
        "avatar": Profile.objects.get(user=request.user).avatar, 
    })


def hot(request):
    questions_, paginates_range = paginate(
        Question.objects.get_hot(), request.GET.get("page"))

    return render(request, "hot.html", {
        "questions": questions_,
        "paginates": paginates_range,
    })


def base(request):
    return redirect("index/")


@login_required
def ajax_like(request):
    try:
        qid = int(request.POST.get("id"))
    except TypeError:
        return JsonResponse(dict())

    type_ = request.POST.get("type")
    if type_ == "question":
        object_class = Question
    elif type_ == "answer":
        object_class = Answer
    else:
        return JsonResponse(dict())

    object_ = get_object_or_404(object_class, id=qid)
    if object_.likes.filter(user=request.user).count() == 0:
        like = Like(
            user=request.user,
            content_object=object_class.objects.get(id=qid)
        )
        like.save()
        object_.likes_count += 1
        object_.save()
    else:
        object_.likes.filter(user=request.user).delete()
        object_.likes_count -= 1
        
    object_.save()

    return JsonResponse({
        "likes_count": object_.likes_count,
    })


@login_required
def ajax_correct(request):
    try:
        qid = int(request.POST.get("id"))
    except TypeError:
        return JsonResponse(dict())

    answer = get_object_or_404(Answer, id=qid)
    if answer.author == request.user:
        answer.is_correct = True
        answer.save()

        return JsonResponse({
            "is_correct": True,
        })
    else:
        return JsonResponse({
            "is_correct": False,
        })


def ajax_search(request):
    search = str(request.POST.get("search")).split(" ")
    query = SearchQuery(search[0])
    for i in range(1, len(search)):
        query |= SearchQuery(search[i])

    vector = SearchVector("title", "text")
    rank = SearchRank(vector, query)
    questions = Question.objects.annotate(rank=rank).order_by("-rank").values_list("title", "id")[0:5]
    return JsonResponse({
        "questions": list(questions),
    })

