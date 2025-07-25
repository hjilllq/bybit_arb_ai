from __future__ import annotations
import asyncio, logging
from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Tuple
import numpy as np, torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import config

logger = logging.getLogger(__name__)

@dataclass
class Roll: obs: deque; acts: deque; rews: deque

class _EdgeEnv:
    def reset(self): return np.array([0.0], dtype=np.float32)
    def step(self, act): return np.array([0.0]), 0.0, True, {}

class ArbitrageStrategyMulti:
    def __init__(self, client: "APIClient"):  # noqa: F821
        self.client = client
        self.policies: Dict[str, PPO] = {}
        self.roll: Dict[str, Roll] = {}
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        for sym in config.TRADE_PAIRS:
            env = DummyVecEnv([_EdgeEnv])
            self.policies[sym] = PPO("MlpPolicy", env, verbose=0, device=device,
                                     n_steps=128, batch_size=64)
            self.roll[sym] = Roll(deque(maxlen=config.RL_BUFFER_CAP),
                                  deque(maxlen=config.RL_BUFFER_CAP),
                                  deque(maxlen=config.RL_BUFFER_CAP))
        asyncio.create_task(self._ppo_trainer())

    async def analyze(self, sym: str) -> Tuple[str, Decimal]:
        bid, ask = await self.client.get_best(sym)
        edge = (bid - ask) / ask - config.SPOT_FEE_RATE - config.FUTURES_FEE_TAKER
        idx, _ = self.policies[sym].predict(np.array([[float(edge)]]), deterministic=True)
        action_map = {0: "hold", 1: "buy_spot", 2: "sell_spot"}
        action = action_map.get(int(idx), "hold")
        self._push_roll(sym, edge, idx)
        return action, Decimal(str(edge))

    def _push_roll(self, sym, edge, idx):
        r = self.roll[sym]; r.obs.append(edge); r.acts.append(idx); r.rews.append(edge)

    async def _ppo_trainer(self):
        while True:
            await asyncio.sleep(config.RL_UPDATE_SEC)
            for sym, roll in self.roll.items():
                if len(roll.obs) < config.RL_MIN_ROLLOUT:
                    continue
                env = self.policies[sym].env
                obs = np.array(roll.obs).reshape(-1, 1)
                acts= np.array(roll.acts).reshape(-1, 1)
                rews= np.array(roll.rews).reshape(-1, 1)
                env.buf_obs[:]  = obs
                env.buf_rew[:]  = rews
                env.buf_act[:]  = acts
                self.policies[sym].learn(total_timesteps=len(obs), reset_num_timesteps=False)
                roll.obs.clear(); roll.acts.clear(); roll.rews.clear()
                logger.info("PPO updated %s (%s steps)", sym, len(obs))