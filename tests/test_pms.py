# -*- coding: utf-8 -*-
import unittest
from app import create_app, db
from app.models import TableInitializer, pms, blog, movie


class PMSTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        # db.drop_all()
        self.app_context.pop()

    def test_init_db(self):
        print 'Insert `pms_permission` with permissions: ...'
        TableInitializer.pms_insert_permissions()
        print 'Insert `pms_role` with roles: root & super_admin & anonymous & default'
        TableInitializer.pms_insert_roles()
        print 'Assign roles with permissions: ...'
        TableInitializer.pms_assign_permissions()
        print 'Insert `pms_user` with: `SUPER_ADMIN_ACCOUNT` (password: 0) ...'
        TableInitializer.pms_insert_administrator()

    """
    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password
    """

    """
    def test_blog_post(self, count=100):
        print 'Insert table blog_poster: (100 posters) ...'
        from random import seed, randint
        import forgery_py
        seed()
        user_count = pms.PMSUser.query.count()
        for i in range(count):
            u = pms.PMSUser.query.offset(randint(0, user_count - 1)).first()
            p = blog.BlogPost(title=forgery_py.lorem_ipsum.title(),
                              body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                              timestamp=forgery_py.date.date(True), author=u)
            db.session.add(p)
            db.session.commit()

    def test_blog_comment(self):
        print 'Insert table blog_comment: None'

    def test_blog_category(self):
        print 'Insert table blog_category: ...'
        blog_category = u'未分类,技术设计,技术笔记,日常笔记,生存技能'
        categories = blog_category.split(u',')
        for c in categories:
            c_category = blog.BlogCategory.query.filter_by(name=c).first()
            if c_category is None:
                c_category = blog.BlogCategory(name=c)
            db.session.add(c_category)
        db.session.commit()

    def test_blog_tag(self):
        print 'Insert table blog_tag: None'

    def test_blog_tagging(self):
        print 'Insert table blog_tagging: None'

    def test_movie_poster(self, count=100):
        print 'Insert table movie_poster: (100 posters) ...'
        import forgery_py
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        seed()
        num_type = movie.MovieType.query.count()
        num_author = pms.PMSUser.query.count()
        for i in range(count):
            p = movie.MoviePoster()
            p.id = 1000001 + i
            p.name = forgery_py.lorem_ipsum.title()
            p.o_name = forgery_py.lorem_ipsum.title()
            p.alias = u'(Empty)'
            p.director = forgery_py.name.full_name()
            p.screenwriter = forgery_py.name.full_name()
            p.performers = forgery_py.name.full_name() + u'/' + forgery_py.name.full_name() + u'/' + forgery_py.name.full_name()
            p.length = u'{}分钟'.format(randint(90, 180))
            p.release_date = forgery_py.date.date().strftime('%Y-%m-%d')
            p.douban_link = u'http://movie.douban.com/' + forgery_py.internet.domain_name()
            p.type_id = randint(0, num_type)
            p.country = forgery_py.address.country()
            p.author_id = randint(0, num_author)
            p.timestamp = forgery_py.date.date(True)
            p.introduction = forgery_py.lorem_ipsum.sentences(randint(1, 5))
            db.session.add(p)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def test_movie_still(self):
        print 'Insert table movie_still: None'

    def test_movie_type(self):
        print 'Insert table movie_type: ...'
        movie_type = u'未定义,动作与历险,儿童与家庭,喜剧,剧情,爱情,恐怖与惊悚,科幻与奇幻,记录与传记,动画,情色,其他'
        types = movie_type.split(u',')
        for t in types:
            t_type = movie.MovieType.query.filter_by(name=t).first()
            if t_type is None:
                t_type = movie.MovieType(name=t)
            db.session.add(t_type)
        db.session.commit()

    def test_movie_tag(self):
        print 'Insert table movie_tag: None'

    def test_movie_tagging(self):
        print 'Insert table movie_tagging: None'
    """
