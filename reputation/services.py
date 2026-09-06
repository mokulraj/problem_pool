from django.db import transaction

from .models import ReputationReward


REWARD_POINTS = {
    ReputationReward.RewardType.PROBLEM_CREATED: 5,
    ReputationReward.RewardType.SOLUTION_PROPOSED: 10,
    ReputationReward.RewardType.UPVOTE_RECEIVED: 2,
    ReputationReward.RewardType.SOLUTION_SELECTED: 25,
    ReputationReward.RewardType.TASK_COMPLETED: 5,
    ReputationReward.RewardType.PROJECT_COMPLETED: 50,
}


@transaction.atomic
def award_points(user, reward_type, reference_id=None):
    points = REWARD_POINTS.get(reward_type)

    if points is None:
        raise ValueError("Invalid reputation reward type.")

    reward, created = ReputationReward.objects.get_or_create(
        user=user,
        reward_type=reward_type,
        reference_id=reference_id,
        defaults={
            "points": points,
        },
    )

    if not created:
        return reward, False

    user.points = user.points + points
    user.save(update_fields=["points"])

    return reward, True