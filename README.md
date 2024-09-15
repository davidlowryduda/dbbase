
# dbbase #

A flexible and simple foundation for other basic sqlite projects that I write.

Here are two demonstrations of how it's used.

```
from dbbase.models import Model, IntegerField, TextField
from dbbase.query import QueryableModel
from dbbase.core import DBBase

class Post(Model, QueryableModel):
    table_name = "posts"
    id = IntegerField(primary_key=True)
    title = TextField(nullable=False)
    content = TextField(nullable=False)

db = DBBase('my_database.db')
db.connect()

Post.create_table(db)

Post.create(db, title="First Post", content="This is the first post")
Post.create(db, title="Second Post", content="This is the second post")
Post.create(db, title="Third Post", content="This is the third post")

posts = Post.objects(db).filter(title="Second Post").all()
for post in posts:
    print(post['title'], post['content'])

post = Post.objects(db).get(id=1)
if post:
    print(f"Post 1: {post['title']} - {post['content']}")

ordered_posts = Post.objects(db).order_by('title').all()
for post in ordered_posts:
    print(post['title'], post['content'])

db.close()
```

or possibly

```
from dbbase.core import *
from dbbase.models import *
from datetime import date

class Post(Model):
    table_name = "posts"
    id = IntegerField(primary_key=True)
    title = TextField(nullable=False)
    content = TextField(nullable=False)
    time = DateField()

db = DBBase('test.db')
db.connect()

Post.create_table(db)

Post.create(db, title="First Post", content="Content", time=datetime.date.today())

posts = Post.all(db)
for post in posts:
    print(post['title'], post['content'], post['time'])

Post.update(db, where={"id": 1}, updates={"title": "Updated title"})
posts = Post.all(db)
for post in posts:
    print(post['title'], post['content'], post['time'])

Post.delete(db, id=1)
posts = Post.all(db)
for post in posts:
    print(post['title'], post['content'], post['time'])
```

I could write actual documentation later. I'm going to use this for a couple of
simple tools.

I note that there is also a small plugin layer.
