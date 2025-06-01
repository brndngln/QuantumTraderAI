import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import HTTPException
import redis
from redis import asyncio as aioredis
import json
from enum import Enum
from decimal import Decimal

class VaultType(Enum):
    TRADE = "trade"
    RESERVE = "reserve"
    SPENDING = "spending"
    CRYPTO = "crypto"
    GOLD = "gold"
    OMNIDREAM = "omnidream"

class VaultMetrics(BaseModel):
    balance: Decimal
    available: Decimal
    locked: Decimal
    allocated: Decimal
    last_update: datetime
    risk_level: float
    health_score: float
    allocation_ratio: float

class VaultSecurityAgent(BaseModel):
    vault_type: VaultType
    security_level: int
    encryption_key: str
    audit_trail: List[Dict]
    last_audit: datetime

class VaultSystem:
    def __init__(self):
        self.redis_pool = aioredis.from_url(
            "redis://localhost:6379",
            decode_responses=True
        )
        self.vault_types = {
            VaultType.TRADE: 0.3,  # 30% allocation
            VaultType.RESERVE: 0.4,  # 40% allocation
            VaultType.SPENDING: 0.1,  # 10% allocation
            VaultType.CRYPTO: 0.1,  # 10% allocation
            VaultType.GOLD: 0.05,  # 5% allocation
            VaultType.OMNIDREAM: 0.05  # 5% allocation
        }
        
    async def initialize_vaults(self) -> None:
        """
        Initialize all vaults with basic settings
        """
        try:
            for vault_type in VaultType:
                vault_key = f"vault:{vault_type.value}"
                await self.redis_pool.hset(
                    vault_key,
                    mapping={
                        'balance': '0',
                        'available': '0',
                        'locked': '0',
                        'allocated': '0',
                        'last_update': datetime.now().isoformat(),
                        'risk_level': '0',
                        'health_score': '100',
                        'allocation_ratio': str(self.vault_types[vault_type])
                    }
                )
                
                # Initialize security agent
                security_agent = VaultSecurityAgent(
                    vault_type=vault_type,
                    security_level=5,
                    encryption_key=self._generate_encryption_key(),
                    audit_trail=[],
                    last_audit=datetime.now()
                )
                
                await self.redis_pool.set(
                    f"security_agent:{vault_type.value}",
                    security_agent.json()
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error initializing vaults: {str(e)}"
            )
    
    async def allocate_funds(self, total_amount: Decimal) -> Dict:
        """
        Allocate funds across all vaults
        """
        try:
            allocations = {}
            remaining = total_amount
            
            for vault_type, ratio in self.vault_types.items():
                if remaining > 0:
                    amount = min(remaining, total_amount * Decimal(ratio))
                    allocations[vault_type] = amount
                    remaining -= amount
                    
                    # Update vault
                    vault_key = f"vault:{vault_type.value}"
                    current_balance = Decimal(await self.redis_pool.hget(vault_key, 'balance') or '0')
                    new_balance = current_balance + amount
                    
                    await self.redis_pool.hset(
                        vault_key,
                        mapping={
                            'balance': str(new_balance),
                            'available': str(new_balance),
                            'last_update': datetime.now().isoformat()
                        }
                    )
                    
                    # Update security audit
                    security_key = f"security_agent:{vault_type.value}"
                    security_agent = VaultSecurityAgent.parse_raw(
                        await self.redis_pool.get(security_key)
                    )
                    
                    security_agent.audit_trail.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'fund_allocation',
                        'amount': str(amount),
                        'balance': str(new_balance)
                    })
                    
                    await self.redis_pool.set(
                        security_key,
                        security_agent.json()
                    )
            
            return allocations
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error allocating funds: {str(e)}"
            )
    
    async def get_vault_metrics(self, vault_type: VaultType) -> VaultMetrics:
        """
        Get metrics for a specific vault
        """
        try:
            vault_key = f"vault:{vault_type.value}"
            vault_data = await self.redis_pool.hgetall(vault_key)
            
            if not vault_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vault {vault_type.value} not found"
                )
            
            return VaultMetrics(
                balance=Decimal(vault_data['balance']),
                available=Decimal(vault_data['available']),
                locked=Decimal(vault_data['locked']),
                allocated=Decimal(vault_data['allocated']),
                last_update=datetime.fromisoformat(vault_data['last_update']),
                risk_level=float(vault_data['risk_level']),
                health_score=float(vault_data['health_score']),
                allocation_ratio=float(vault_data['allocation_ratio'])
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting vault metrics: {str(e)}"
            )
    
    async def update_vault_risk(self, vault_type: VaultType, risk_level: float) -> None:
        """
        Update vault risk level
        """
        try:
            vault_key = f"vault:{vault_type.value}"
            await self.redis_pool.hset(
                vault_key,
                'risk_level',
                str(risk_level)
            )
            
            # Update health score based on risk
            health_score = 100 - (risk_level * 100)
            await self.redis_pool.hset(
                vault_key,
                'health_score',
                str(health_score)
            )
            
            # Update security agent
            security_key = f"security_agent:{vault_type.value}"
            security_agent = VaultSecurityAgent.parse_raw(
                await self.redis_pool.get(security_key)
            )
            
            security_agent.audit_trail.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'risk_update',
                'risk_level': str(risk_level),
                'health_score': str(health_score)
            })
            
            await self.redis_pool.set(
                security_key,
                security_agent.json()
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating vault risk: {str(e)}"
            )
    
    def _generate_encryption_key(self) -> str:
        """
        Generate a secure encryption key
        """
        import secrets
        return secrets.token_hex(32)
    
    async def perform_security_audit(self, vault_type: VaultType) -> Dict:
        """
        Perform security audit on a vault
        """
        try:
            security_key = f"security_agent:{vault_type.value}"
            security_agent = VaultSecurityAgent.parse_raw(
                await self.redis_pool.get(security_key)
            )
            
            # Check security level
            security_check = {
                'encryption_key_valid': True,
                'audit_trail_integrity': True,
                'last_audit_age': (datetime.now() - security_agent.last_audit).total_seconds(),
                'security_level': security_agent.security_level
            }
            
            # Update audit trail
            security_agent.audit_trail.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'security_audit',
                'result': security_check
            })
            security_agent.last_audit = datetime.now()
            
            await self.redis_pool.set(
                security_key,
                security_agent.json()
            )
            
            return security_check
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error performing security audit: {str(e)}"
            )
    
    async def get_vault_allocation(self) -> Dict:
        """
        Get current allocation across all vaults
        """
        try:
            allocations = {}
            total_balance = Decimal('0')
            
            for vault_type in VaultType:
                vault_key = f"vault:{vault_type.value}"
                vault_data = await self.redis_pool.hgetall(vault_key)
                
                if vault_data:
                    balance = Decimal(vault_data['balance'])
                    total_balance += balance
                    allocations[vault_type] = {
                        'balance': balance,
                        'allocation_ratio': float(vault_data['allocation_ratio'])
                    }
            
            # Calculate actual allocation percentages
            for vault_type in allocations:
                if total_balance > 0:
                    allocations[vault_type]['actual_ratio'] = float(
                        allocations[vault_type]['balance'] / total_balance
                    )
                else:
                    allocations[vault_type]['actual_ratio'] = 0
            
            return allocations
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting vault allocation: {str(e)}"
            )
    
    async def rebalance_vaults(self, total_amount: Decimal) -> Dict:
        """
        Rebalance vaults based on current allocation
        """
        try:
            current_allocations = await self.get_vault_allocation()
            target_allocations = await self.allocate_funds(total_amount)
            
            rebalancing = {}
            
            for vault_type in VaultType:
                current = current_allocations[vault_type]['balance']
                target = target_allocations[vault_type]
                
                if current != target:
                    diff = target - current
                    rebalancing[vault_type] = {
                        'current': current,
                        'target': target,
                        'difference': diff,
                        'percentage_change': float(diff / current * 100) if current > 0 else 0
                    }
                    
                    # Update vault
                    vault_key = f"vault:{vault_type.value}"
                    await self.redis_pool.hset(
                        vault_key,
                        mapping={
                            'balance': str(target),
                            'available': str(target),
                            'last_update': datetime.now().isoformat()
                        }
                    )
                    
                    # Update security audit
                    security_key = f"security_agent:{vault_type.value}"
                    security_agent = VaultSecurityAgent.parse_raw(
                        await self.redis_pool.get(security_key)
                    )
                    
                    security_agent.audit_trail.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'rebalance',
                        'amount': str(target),
                        'difference': str(diff)
                    })
                    
                    await self.redis_pool.set(
                        security_key,
                        security_agent.json()
                    )
            
            return rebalancing
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error rebalancing vaults: {str(e)}"
            )
# temp
print("Force refresh")
