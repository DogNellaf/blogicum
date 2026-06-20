from django.contrib import admin

from .models import Category, Comment, Location, Post

# В админке пустые значения полей отображаются этой строкой.
admin.site.empty_value_display = 'Не задано'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    list_editable = ('is_published',)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published',)
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = (CommentInline,)
    list_display = ('title', 'author', 'category', 'location', 'is_published',
                    'pub_date', 'created_at')
    list_editable = ('is_published', 'category', 'location')
    search_fields = ('title', 'text')
    list_filter = ('category', 'location', 'is_published', 'pub_date')
    date_hierarchy = 'pub_date'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'text', 'created_at')
    search_fields = ('text', 'author__username', 'post__title')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
