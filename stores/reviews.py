from django.contrib.auth.models import User
from stores.models import Product, Review
from rest_framework import status 
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import ReviewSerializer  # Make sure you have this serializer


@api_view(["GET"])
def get_product_reviews(request, product_id):
    user_id = request.GET.get("user_id")  # get from query string
    try:
        product = Product.objects.get(id=product_id)
        reviews = Review.objects.filter(product=product).order_by("-created_at")
        user = User.objects.filter(id=user_id).first() if user_id else None
        serializer = ReviewSerializer(
            reviews, many=True, context={"request_user": user}
        )
        return Response(serializer.data, status=200)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)


@api_view(["POST"])
def react_review(request, review_id):
    user_id = request.data.get("user_id")
    action = request.data.get("action")

    try:
        user = User.objects.get(id=user_id)
        review = Review.objects.get(id=review_id)

        if action == "like":
            review.dislikes.remove(user)
            review.likes.add(user)
        elif action == "dislike":
            review.likes.remove(user)
            review.dislikes.add(user)

        return Response(
            {"likes": review.like_count(), "dislikes": review.dislike_count()},
            status=200,
        )
    except (User.DoesNotExist, Review.DoesNotExist):
        return Response({"error": "Invalid user or review"}, status=404)


@api_view(["POST"])
def create_review(request, product_id):
    user_id = request.data.get("user_id")
    rating = request.data.get("rating")
    comment = request.data.get("comment")

    # 🔒 Validate input
    if not all([user_id, rating, comment]):
        return Response({"error": "Missing fields"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    # 🧠 Optional: prevent duplicate reviews per product per user
    existing = Review.objects.filter(user=user, product=product).first()
    if existing:
        return Response({"error": "You already reviewed this product."}, status=400)

    # ✅ Save the review
    Review.objects.create(
        user=user, product=product, rating=int(rating), comment=comment.strip()
    )

    return Response({"message": "Review created successfully"}, status=201)