from app import views


def right_side(request):
    return {
        "tags": views.get_top_tags(),
        "members": views.get_top_members(),
        "user": request.user,
    }
