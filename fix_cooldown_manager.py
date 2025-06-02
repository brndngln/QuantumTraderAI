def fix_cooldown_manager():
    file_path = 'backend/utils/cooldown_manager.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix get_config indentation
    content = content.replace('    async def get_config(self, strategy_id: str) -> CooldownConfig:\n        """\n        Get cooldown config for strategy\n        """\n        try:\n            config_data = await self.redis_pool.get(f"cooldown_config:{strategy_id}")\n            if config_data:\n                return CooldownConfig(**json.loads(config_data))\n            return CooldownConfig()',
                           '    async def get_config(self, strategy_id: str) -> CooldownConfig:\n        """\n        Get cooldown config for strategy\n        """\n        try:\n            config_data = await self.redis_pool.get(f"cooldown_config:{strategy_id}")\n            if config_data:\n                return CooldownConfig(**json.loads(config_data))\n            return CooldownConfig()')
    
    # Fix set_config indentation
    content = content.replace('    async def set_config(self, strategy_id: str, config: CooldownConfig) -> None:\n        """\n        Set cooldown config for strategy\n        """\n        try:\n            await self.redis_pool.set(\n                f"cooldown_config:{strategy_id}",\n                json.dumps(config.dict())\n            )',
                           '    async def set_config(self, strategy_id: str, config: CooldownConfig) -> None:\n        """\n        Set cooldown config for strategy\n        """\n        try:\n            await self.redis_pool.set(\n                f"cooldown_config:{strategy_id}",\n                json.dumps(config.dict())\n            )')
    
    # Fix reset_cooldown indentation
    content = content.replace('    async def reset_cooldown(self, strategy_id: str) -> None:\n        """\n        Reset cooldown for strategy\n        """\n        try:\n            await self.redis_pool.delete(f"cooldown_config:{strategy_id}")',
                           '    async def reset_cooldown(self, strategy_id: str) -> None:\n        """\n        Reset cooldown for strategy\n        """\n        try:\n            await self.redis_pool.delete(f"cooldown_config:{strategy_id}")')
    
    # Fix try-except blocks
    content = content.replace('        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error getting cooldown config: {str(e)}"\n            )',
                           '        except Exception as e:\n            raise HTTPException(\n                status_code=500,\n                detail=f"Error getting cooldown config: {str(e)}"\n            )')
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_cooldown_manager()
