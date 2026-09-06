from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from solutions.models import Solution

from .forms import CommentForm
from .models import Comment


@login_required
def comment_create(request):

    if request.method != "POST":
        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "problems:list"
        )

    problem_id = request.POST.get(
        "problem_id"
    )

    solution_id = request.POST.get(
        "solution_id"
    )

    if problem_id and solution_id:
        messages.error(
            request,
            "Invalid comment target.",
        )

        return redirect(
            "problems:list"
        )

    comment = Comment(
        user=request.user
    )

    if problem_id:

        from problems.models import Problem

        problem = get_object_or_404(
            Problem,
            pk=problem_id,
        )

        comment.problem = problem

    elif solution_id:

        solution = get_object_or_404(
            Solution,
            pk=solution_id,
        )

        comment.solution = solution

    else:

        messages.error(
            request,
            "A problem or solution is required.",
        )

        return redirect(
            "problems:list"
        )

    form = CommentForm(
        request.POST,
        instance=comment,
    )

    if not form.is_valid():

        print(
            "COMMENT FORM ERRORS:",
            form.errors
        )

        messages.error(
            request,
            "Please enter a valid comment.",
        )

        return redirect(
            request.POST.get(
                "next",
                "problems:list"
            )
        )

    form.save()

    messages.success(
        request,
        "Comment added successfully.",
    )

    return redirect(
        request.POST.get(
            "next",
            request.META.get(
                "HTTP_REFERER",
                "/"
            ),
        )
    )


@login_required
def comment_edit(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk,
    )

    if comment.user != request.user:

        return HttpResponseForbidden(
            "You do not have permission to edit this comment."
        )

    if request.method == "POST":

        form = CommentForm(
            request.POST,
            instance=comment,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Comment updated successfully.",
            )

            return comment_redirect(comment)

    else:

        form = CommentForm(
            instance=comment,
        )

    return render(
        request,
        "comments/comment_form.html",
        {
            "form": form,
            "comment": comment,
            "page_title": "Edit Comment",
            "submit_text": "Save Comment",
        },
    )


@login_required
def comment_delete(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk,
    )

    if comment.user != request.user:

        return HttpResponseForbidden(
            "You do not have permission to delete this comment."
        )

    if request.method != "POST":

        return HttpResponseForbidden(
            "Comment deletion requires a POST request."
        )

    target = comment_redirect(
        comment
    )

    comment.delete()

    messages.success(
        request,
        "Comment deleted successfully.",
    )

    return target


def comment_redirect(comment):

    if comment.solution_id:

        return redirect(
            "solutions:detail",
            pk=comment.solution_id,
        )

    return redirect(
        "problems:detail",
        pk=comment.problem_id,
    )