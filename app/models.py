from django.db import models
from django.contrib.auth import models as DjangoUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.postgres.indexes import GinIndex
from datetime import datetime


class Profile(models.Model):
    user = models.OneToOneField(
        DjangoUser.User,
        on_delete=models.CASCADE,
        db_index=True)
    avatar = models.CharField(max_length=120, default="/img/photo.jpg")


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name=u"Tag", unique=True)

    def __str__(self):
        return self.name


class Like(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        self.content_object.like(self)
        super(Like, self).save(*args, **kwargs)

    user = models.ForeignKey(
        DjangoUser.User, on_delete=models.CASCADE, db_index=True)


class QuestionManager(models.Manager):
    def get_by_tag(self, tag):
        return super().get_queryset().filter(tags=tag)

    def get_hot(self):
        return super().get_queryset().order_by('-likes_count')


class Question(models.Model):
    title = models.CharField(max_length=120, verbose_name=u"Question title")
    text = models.TextField(verbose_name=u"Question field")

    likes = GenericRelation(Like, related_query_name='question')

    author = models.ForeignKey(
        DjangoUser.User,
        on_delete=models.CASCADE,
        db_index=True
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True
    )
    create_date = models.DateTimeField(
        default=datetime.now,
        verbose_name=u"Время создания вопроса"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=u"Доступность вопроса"
    )

    likes_count = models.PositiveIntegerField(default=0)
    answers_count = models.PositiveIntegerField(default=0)
    photo = models.CharField(default="/img/photo.jpg", max_length=120)

    objects = QuestionManager()

    def like(self, like_object):
        if like_object not in Like.objects.all():
            self.likes_count += 1
            self.save()

    def add_answer(self, answer_object):
        if answer_object not in Answer.objects.all():
            self.answers_count += 1
            self.save()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.photo = Profile.objects.get(user=self.author).avatar
        super(Question, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-create_date']
        indexes = [GinIndex(fields=['title', 'text'])]


class AnswerManager(models.Manager):
    def get_by_question(self, question):
        return super().get_queryset().filter(question=question)


class Answer(models.Model):
    text = models.TextField(verbose_name=u"Answer field")
    likes_count = models.PositiveIntegerField(default=0)
    photo = models.CharField(default="/img/photo.jpg", max_length=120)
    is_correct = models.BooleanField(default=False)

    likes = GenericRelation(Like, related_query_name='answer')

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        db_index=True)

    author = models.ForeignKey(
        DjangoUser.User,
        on_delete=models.CASCADE,
        db_index=True)

    objects = AnswerManager()

    def save(self, *args, **kwargs):
        self.question.add_answer(self)
        self.photo = Profile.objects.get(user=self.author).avatar
        super(Answer, self).save(*args, **kwargs)

    def like(self, like_object):
        if like_object not in Like.objects.all():
            self.likes_count += 1
            super(Answer, self).save()

