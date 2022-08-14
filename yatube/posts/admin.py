from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'description',
    )
    search_fields = ('title', )
    list_filter = ('title', )
    empty_value_display = '-пусто-'
    prepopulated_fields = {'slug': ('title', )}


class CommentAdmin(admin.TabularInline):
    model = Comment
    list_display = (
        'pk',
        'text',
        'post',
        'author',
        'created',
    )
    search_fields = (
        'text',
        'author',
    )
    list_filter = (
        'text',
        'author',
    )
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    inlines = [CommentAdmin]
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group', )
    search_fields = ('text', )
    list_filter = ('pub_date', )
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Follow, FollowAdmin)
