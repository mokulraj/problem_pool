from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from problems.models import Problem
from notifications.models import Notification

from .forms import SolutionForm
from .models import Solution
from .models import Vote


def solution_detail(request, pk):

    solution = get_object_or_404(
        Solution.objects.select_related(
            "problem",
            "proposed_by",
        ).prefetch_related(
            "comments__user",
        ),
        pk=pk,
    )

    user_vote = None

    if request.user.is_authenticated:

        user_vote = (
            Vote.objects
            .filter(
                user=request.user,
                solution=solution,
            )
            .values_list(
                "vote_type",
                flat=True,
            )
            .first()
        )

    comments = (
        solution.comments
        .select_related("user")
        .order_by("created_at")
    )

    return render(
        request,
        "solutions/solution_detail.html",
        {
            "solution": solution,
            "user_vote": user_vote,
            "comments": comments,
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
                    solution_count=F("solution_count") + 1
                )

                # -------------------------------------------------
                # NOTIFY PROBLEM OWNER
                # -------------------------------------------------

                if problem.created_by != request.user:

                    Notification.objects.create(
                        recipient=problem.created_by,
                        message=(
                            f"{request.user.get_full_name() or request.user.username} "
                            f"proposed a solution for your problem: "
                            f"{problem.title}"
                        ),
                        notification_type=(
                            Notification.NotificationType.SOLUTION_PROPOSED
                        ),
                        related_problem=problem,
                        related_solution=solution,
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
        Solution.objects.select_related(
            "proposed_by",
            "problem",
        ),
        pk=pk,
    )

    # ---------------------------------------------------------
    # USER CANNOT VOTE ON OWN SOLUTION
    # ---------------------------------------------------------

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

    notify_solution_owner = False

    with transaction.atomic():

        vote = Vote.objects.filter(
            user=request.user,
            solution=solution,
        ).first()

        # =====================================================
        # EXISTING VOTE
        # =====================================================

        if vote:

            # -------------------------------------------------
            # SAME VOTE = REMOVE
            # -------------------------------------------------

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

            # -------------------------------------------------
            # OPPOSITE VOTE = CHANGE
            # -------------------------------------------------

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

                # DOWN -> UP
                if vote_type == Vote.VoteType.UP:
                    notify_solution_owner = True

        # =====================================================
        # NEW VOTE
        # =====================================================

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

                notify_solution_owner = True

            else:

                Solution.objects.filter(
                    pk=solution.pk
                ).update(
                    downvotes=F("downvotes") + 1
                )

            action = "added"

        # =====================================================
        # REFRESH SOLUTION VALUES
        # =====================================================

        solution.refresh_from_db()

        solution.score = (
            solution.upvotes -
            solution.downvotes
        )

        solution.save(
            update_fields=[
                "score"
            ]
        )

        # =====================================================
        # CREATE UPVOTE NOTIFICATION
        # =====================================================

        if notify_solution_owner:

            existing_upvote_notification = Notification.objects.filter(
                recipient=solution.proposed_by,
                notification_type=Notification.NotificationType.VOTE,
                related_solution=solution,
                related_problem=solution.problem,
                message__startswith=(
                    f"{request.user.get_full_name() or request.user.username} "
                    f"upvoted your solution:"
                ),
            ).exists()

            if not existing_upvote_notification:

                Notification.objects.create(
                    recipient=solution.proposed_by,
                    message=(
                        f"{request.user.get_full_name() or request.user.username} "
                        f"upvoted your solution: "
                        f"{solution.title}"
                    ),
                    notification_type=(
                        Notification.NotificationType.VOTE
                    ),
                    related_solution=solution,
                    related_problem=solution.problem,
                )

    # =========================================================
    # CURRENT USER VOTE
    # =========================================================

    current_vote = (
        Vote.objects
        .filter(
            user=request.user,
            solution=solution,
        )
        .values_list(
            "vote_type",
            flat=True,
        )
        .first()
    )

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


@login_required
def select_solution(request, pk):

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request.",
        )

        return redirect(
            "solutions:detail",
            pk=pk,
        )

    solution = get_object_or_404(
        Solution.objects.select_related(
            "problem",
            "proposed_by",
        ),
        pk=pk,
    )

    problem = solution.problem

    if problem.created_by != request.user:

        messages.error(
            request,
            "Only the problem owner can select a solution.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.REJECTED:

        messages.error(
            request,
            "A rejected solution cannot be selected.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    if solution.status == Solution.Status.SELECTED:

        messages.info(
            request,
            "This solution is already selected.",
        )

        return redirect(
            "solutions:detail",
            pk=solution.pk,
        )

    with transaction.atomic():

        # -----------------------------------------------------
        # PREVIOUS SELECTED SOLUTION
        # -----------------------------------------------------

        Solution.objects.filter(
            problem=problem,
            status=Solution.Status.SELECTED,
        ).exclude(
            pk=solution.pk,
        ).update(
            status=Solution.Status.SHORTLISTED,
        )

        # -----------------------------------------------------
        # SELECT CURRENT SOLUTION
        # -----------------------------------------------------

        solution.status = Solution.Status.SELECTED

        solution.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # -----------------------------------------------------
        # UPDATE PROBLEM
        # -----------------------------------------------------

        problem.status = Problem.Status.IN_PROGRESS

        problem.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # -----------------------------------------------------
        # NOTIFY SOLUTION AUTHOR
        # -----------------------------------------------------

        if solution.proposed_by != request.user:

            existing_selected_notification = Notification.objects.filter(
                recipient=solution.proposed_by,
                notification_type=(
                    Notification.NotificationType.SOLUTION_SELECTED
                ),
                related_solution=solution,
                related_problem=problem,
            ).exists()

            if not existing_selected_notification:

                Notification.objects.create(
                    recipient=solution.proposed_by,
                    message=(
                        f"Your solution '{solution.title}' "
                        f"was selected for the problem "
                        f"'{problem.title}'."
                    ),
                    notification_type=(
                        Notification.NotificationType.SOLUTION_SELECTED
                    ),
                    related_solution=solution,
                    related_problem=problem,
                )

    messages.success(
        request,
        "Solution selected successfully. You can now convert it into a project.",
    )

    return redirect(
        "solutions:detail",
        pk=solution.pk,
    )


def solution_list(request):

    # =========================================================
    # GET FILTER VALUES
    # =========================================================

    selected_category = request.GET.get(
        "category",
        "",
    )

    selected_status = request.GET.get(
        "status",
        "",
    )

    selected_sort = request.GET.get(
        "sort",
        "newest",
    )

    # =========================================================
    # BASE QUERY
    # =========================================================

    solutions = (
        Solution.objects
        .select_related(
            "problem",
            "proposed_by",
        )
    )

    # =========================================================
    # CATEGORY FILTER
    # =========================================================

    if selected_category:

        solutions = solutions.filter(
            problem__category=selected_category
        )

    # =========================================================
    # STATUS FILTER
    # =========================================================

    if selected_status:

        solutions = solutions.filter(
            status=selected_status
        )

    # =========================================================
    # SORTING
    # =========================================================

    if selected_sort == "most_votes":

        solutions = solutions.order_by(
            "-upvotes",
            "-created_at",
        )

    elif selected_sort == "most_viewed":

        solutions = solutions.order_by(
            "-problem__views",
            "-created_at",
        )

    else:

        solutions = solutions.order_by(
            "-created_at",
        )

    # =========================================================
    # CATEGORY OPTIONS
    # =========================================================

    categories = Problem.Category.choices

    # =========================================================
    # STATUS OPTIONS
    # =========================================================

    statuses = Solution.Status.choices

    return render(
        request,
        "solutions/solution_list.html",
        {
            "solutions": solutions,
            "categories": categories,
            "statuses": statuses,
            "selected_category": selected_category,
            "selected_status": selected_status,
            "selected_sort": selected_sort,
        },
    )