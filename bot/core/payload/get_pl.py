import asyncio

import os
async def get_payload(game_id, points, freeze):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        proc = await asyncio.create_subprocess_exec(
            'node', 'blum.mjs', game_id, str(points), str(freeze),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=script_dir
        )
        stdout, stderr = await proc.communicate()
        if stderr:
            print(f"Subprocess error: {stderr.decode().strip()}")
        return stdout.decode().strip()
    except Exception as e:
        print(f"Exception in get_payload: {e}")
        return None


async def main():
    game_id = "f79adb73-6518-442c-9a87-a705d5dffb97"
    points = 180
    freeze = 3

    result_payload = await get_payload(game_id, points, freeze)
    print(result_payload)

if __name__ == "__main__":
    asyncio.run(main())
