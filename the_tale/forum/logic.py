# coding: utf-8

from dext.utils.decorators import nested_commit_on_success

from forum.models import SubCategory, Thread, Post, MARKUP_METHOD

@nested_commit_on_success
def create_thread(subcategory, caption, author, text, markup_method=MARKUP_METHOD.POSTMARKUP):

    if isinstance(subcategory, int):
        subcategory = SubCategory.objects.get(id=subcategory)

    thread = Thread.objects.create(subcategory=subcategory,
                                   caption=caption,
                                   author=author,
                                   posts_count=0)

    post = Post.objects.create(thread=thread,
                               author=author,
                               markup_method=markup_method,
                               text=text)

    subcategory.threads_count = Thread.objects.filter(subcategory=subcategory).count()
    subcategory.posts_count = sum(Thread.objects.filter(subcategory=subcategory).values_list('posts_count', flat=True))
    subcategory.updated_at = post.created_at
    subcategory.save()

    return thread
