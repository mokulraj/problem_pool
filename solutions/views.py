from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from problems.models import Problem

from .forms import SolutionForm
from .models import Solution
from .models import Vote

def solution_detail(request, pk):
    
    solution = get_object_or_404(
        Solution.objects.select_related(
            "problem",
            "proposed_by",
        ),
        pk=pk,
    )

    user_vote = None

    if request.user.is_authenticated:

        user_vote = Vote.objects.filter(
            user=request.user,
            solution=solution,
        ).values_list(
            "vote_type",
            flat=True,
        ).first()

    return render(
        request,
        "solutions/solution_detail.html",
        {
            "solution": solution,
            "user_vote": user_vote,
        },
    )

@login_required
def solution_create(request):

    problem_id = request.GET.get("problem")

    if not problem_id:
        messages.error(
            request,
            "A problem is required before submitting a solution.",
        )

        return redirect(
            "problems:list"
        )

    problem = get_object_or_404(
        Problem,
        pk=problem_id,
    )

    if problem.status in [
        Problem.Status.SOLVED,
        Problem.Status.CLOSED,
    ]:
        messages.warning(
            request,
            "Solutions cannot be submitted to a closed or solved problem.",
        )

        return redirect(
            "problems:detail",
            pk=problem.pk,
        )

    if request.method == "POST":

        form = SolutionForm(
            request.POST
        )

        if form.is_valid():

            with transaction.atomic():

                solution = form.save(
                    commit=False
                )

                solution.problem = problem
                solution.proposed_by = request.user

                solution.save()

                Problem.objects.filter(
                    pk=problem.pk
                ).update(
                    solution_count=problem.solution_count + 1
                )

            messages.success(
                request,
                "Solution submitted successfully.",
            )

            return redirect(
                "solutions:detail",
                pk=solution.pk,
            )

    else:

        form = SolutionForm()


    return render(
        request,
        "solutions/solution_form.html",
        {
            "form": form,
            "problem": problem,
            "page_title": "Propose a Solution",
            "submit_text": "Submit Solution",
        },
    )


@login_required
def solution_edit(request, pk):

    solution = get_object_or_404(
        Solution,
        pk=pk,
    )

    if solution.proposed_by != request.user:

        messages.error(
            request,
            "You do not have permission to edit this solution.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.SELECTED:

        messages.warning(
            request,
            "A selected solution cannot be edited.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if request.method == "POST":

        form = SolutionForm(
            request.POST,
            instance=solution,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Solution updated successfully.",
            )

            return redirect(
                "solutions:detail",
                pk=solution.pk,
            )

    else:

        form = SolutionForm(
            instance=solution,
        )


    return render(
        request,
        "solutions/solution_form.html",
        {
            "form": form,
            "problem": solution.problem,
            "solution": solution,
            "page_title": "Edit Solution",
            "submit_text": "Save Changes",
        },
    )


@login_required
def solution_delete(request, pk):

    solution = get_object_or_404(
        Solution,
        pk=pk,
    )

    if solution.proposed_by != request.user:

        messages.error(
            request,
            "You do not have permission to delete this solution.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.SELECTED:

        messages.warning(
            request,
            "A selected solution cannot be deleted.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if request.method == "POST":

        problem_id = solution.problem_id

        solution.delete()

        Problem.objects.filter(
            pk=problem_id,
            solution_count__gt=0,
        ).update(
            solution_count=F("solution_count") - 1
        )

        messages.success(
            request,
            "Solution deleted successfully.",
        )

        return redirect(
            "problems:detail",
            pk=problem_id,
        )


    return render(
        request,
        "solutions/solution_confirm_delete.html",
        {
            "solution": solution,
        },
    )
    
    
@login_required
def vote_solution(request, pk):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method.",
            },
            status=405,
        )


    solution = get_object_or_404(
        Solution,
        pk=pk,
    )


    # A user should not vote on their own solution.
    if solution.proposed_by == request.user:

        return JsonResponse(
            {
                "success": False,
                "message": "You cannot vote on your own solution.",
            },
            status=403,
        )


    vote_type = request.POST.get(
        "vote_type"
    )


    valid_vote_types = {
        Vote.VoteType.UP,
        Vote.VoteType.DOWN,
    }


    if vote_type not in valid_vote_types:

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid vote type.",
            },
            status=400,
        )


    with transaction.atomic():

        vote = Vote.objects.filter(
            user=request.user,
            solution=solution,
        ).first()


        # ----------------------------------------------------
        # EXISTING VOTE
        # ----------------------------------------------------

        if vote:

            # Clicking the same vote removes it.
            if vote.vote_type == vote_type:

                vote.delete()

                if vote_type == Vote.VoteType.UP:

                    Solution.objects.filter(
                        pk=solution.pk,
                        upvotes__gt=0,
                    ).update(
                        upvotes=F("upvotes") - 1
                    )

                else:

                    Solution.objects.filter(
                        pk=solution.pk,
                        downvotes__gt=0,
                    ).update(
                        downvotes=F("downvotes") - 1
                    )

                action = "removed"

            # Clicking the opposite vote changes it.
            else:

                old_vote_type = vote.vote_type

                vote.vote_type = vote_type
                vote.save(
                    update_fields=[
                        "vote_type"
                    ]
                )

                if old_vote_type == Vote.VoteType.UP:

                    Solution.objects.filter(
                        pk=solution.pk,
                        upvotes__gt=0,
                    ).update(
                        upvotes=F("upvotes") - 1
                    )

                    Solution.objects.filter(
                        pk=solution.pk
                    ).update(
                        downvotes=F("downvotes") + 1
                    )

                else:

                    Solution.objects.filter(
                        pk=solution.pk,
                        downvotes__gt=0,
                    ).update(
                        downvotes=F("downvotes") - 1
                    )

                    Solution.objects.filter(
                        pk=solution.pk
                    ).update(
                        upvotes=F("upvotes") + 1
                    )

                action = "changed"


        # ----------------------------------------------------
        # NEW VOTE
        # ----------------------------------------------------

        else:

            Vote.objects.create(
                user=request.user,
                solution=solution,
                vote_type=vote_type,
            )

            if vote_type == Vote.VoteType.UP:

                Solution.objects.filter(
                    pk=solution.pk
                ).update(
                    upvotes=F("upvotes") + 1
                )

            else:

                Solution.objects.filter(
                    pk=solution.pk
                ).update(
                    downvotes=F("downvotes") + 1
                )

            action = "added"


        # Refresh values after F() updates.
        solution.refresh_from_db()

        solution.score = (
            solution.upvotes -
            solution.downvotes
        )

        solution.save(
            update_fields=["score"]
        )


    current_vote = Vote.objects.filter(
        user=request.user,
        solution=solution,
    ).values_list(
        "vote_type",
        flat=True,
    ).first()


    return JsonResponse(
        {
            "success": True,
            "action": action,
            "upvotes": solution.upvotes,
            "downvotes": solution.downvotes,
            "score": solution.score,
            "user_vote": current_vote,
        }
    )