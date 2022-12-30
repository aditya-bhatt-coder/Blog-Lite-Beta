import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Post, User, Comment, Like, followers
from . import db

views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
@login_required
def home():
    followed = Post.query.join(
            followers, (followers.c.followed_id == Post.author)).filter(
                followers.c.follower_id == current_user.id)
    own = Post.query.filter_by(id=current_user.id)
    posts = followed.union(own).order_by(Post.date_created.desc())
    return render_template("home.html", user=current_user, posts=posts)


@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            f = request.files['file']
            filename = secure_filename(f.filename)
            f.save(os.path.join(views.root_path,'static/uploads', filename))
            
            post = Post(text=text, image=filename, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)


@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    following_count = user.followed.filter(followers.c.follower_id == user.id).count()
    follower_count = user.followers.filter(followers.c.followed_id == user.id).count()
    return render_template("posts.html", user=current_user, posts=posts, username=username, follower_count=follower_count, following_count=following_count)


back_username_global = None
@views.route("/follower/<username>")
@login_required
def follower(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    global back_username_global
    back_username_global = username
    follower = user.followers.filter(followers.c.followed_id == user.id).all()
    current_user_following = current_user.followed.filter(followers.c.follower_id == current_user.id).all()
    return render_template("follower.html", user=current_user, username=username, follower=follower, current_user_following=current_user_following)


@views.route("/follower/follow/<user_id>")
@login_required
def follower_follow(user_id):
    user_to_be_followed = User.query.filter_by(id=user_id).first()
    follow = current_user.followed.filter(followers.c.followed_id == user_to_be_followed.id).all()

    if not user_to_be_followed:
        flash('User does not exist.', category='error')
    elif follow: #already followed
        current_user.followed.remove(user_to_be_followed)
        db.session.commit()
    else:
        current_user.followed.append(user_to_be_followed)
        db.session.commit()
    global back_username_global
    return redirect(url_for('views.follower',username=back_username_global))


@views.route("/following/<username>")
@login_required
def following(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    global back_username_global
    back_username_global = username
    following = user.followed.filter(followers.c.follower_id == user.id).all()
    current_user_following = current_user.followed.filter(followers.c.follower_id == current_user.id).all()
    return render_template("following.html", user=current_user, username=username, following=following, current_user_following=current_user_following)


@views.route("/following/follow/<user_id>")
@login_required
def following_follow(user_id):
    user_to_be_followed = User.query.filter_by(id=user_id).first()
    follow = current_user.followed.filter(followers.c.followed_id == user_to_be_followed.id).all()

    if not user_to_be_followed:
        flash('User does not exist.', category='error')
    elif follow: #already followed
        current_user.followed.remove(user_to_be_followed)
        db.session.commit()
    else:
        current_user.followed.append(user_to_be_followed)
        db.session.commit()
    global back_username_global
    return redirect(url_for('views.following',username=back_username_global))


@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))


@views.route("/like-post/<post_id>", methods=['GET'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()

    if not post:
        #return jsonify({'error': 'Post does not exist.'}, 400)
        flash('Post does not exist.', category='error')
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    #return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})
    return redirect(url_for('views.home'))


query_str_global = str()
@views.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    global query_str_global
    if request.method == 'POST':
        query_str_global = request.form["query_str"]
    results = User.query.filter(User.username.like('%' + query_str_global + '%')).all()
    (friend_list, non_friend_list) = ([],[])
    if current_user in results:
        results.remove(current_user)
    for user in results:
        if current_user.followed.filter(followers.c.followed_id == user.id).count() > 0:
            friend_list.append(user)
        else:
            non_friend_list.append(user)
    return render_template("search.html", user=current_user, query_str=query_str_global, results=results, friend_list=friend_list, non_friend_list=non_friend_list)


@views.route("/follow/<user_id>")
@login_required
def follow(user_id):
    user_to_be_followed = User.query.filter_by(id=user_id).first()
    follow = current_user.followed.filter(followers.c.followed_id == user_to_be_followed.id).all()

    if not user_to_be_followed:
        flash('User does not exist.', category='error')
    elif follow: #already followed
        current_user.followed.remove(user_to_be_followed)
        db.session.commit()
    else:
        current_user.followed.append(user_to_be_followed)
        db.session.commit()
    
    return redirect(url_for('views.search'))