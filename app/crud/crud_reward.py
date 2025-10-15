from sqlalchemy.orm import Session
from app.models.reward import Reward
from app.schemas.reward import RewardCreate

def create_reward(db: Session, reward: RewardCreate):
    db_reward = Reward(**reward.dict())
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

def get_rewards(db: Session):
    return db.query(Reward).all()

def get_reward(db: Session, reward_id: int):
    return db.query(Reward).filter(Reward.id == reward_id).first()

def delete_reward(db: Session, reward_id: int):
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if reward:
        db.delete(reward)
        db.commit()
        return reward
    return None
