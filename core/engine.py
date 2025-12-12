#!/usr/bin/env python3
# Module: engine.py

#!/usr/bin/env python3
# Module: Engine
# Author: Sanchez (The Orchestrator)
# Purpose: Abstracting away the threading chaos.

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Any, Optional
from core.config import config
from core.logger import logger

# 📊 Try to import tqdm for a pro progress bar, fallback if missing
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

class Engine:
    """
    The Playmaker. Handles threading, progress bars, and CLI arguments.
    """

    def get_arg_parser(self, description: str) -> argparse.ArgumentParser:
        """
        Returns a parser with the standard 'Sanchez Arsenal' arguments.
        """
        parser = argparse.ArgumentParser(description=description)
        
        # Standard args for every tool
        parser.add_argument("-t", "--threads", type=int, default=config.THREADS, 
                          help=f"Number of threads (default: {config.THREADS})")
        parser.add_argument("-o", "--output", type=str, 
                          help="Save valid hits to a file")
        
        return parser

    def run(self, 
            task_function: Callable, 
            targets: Iterable[Any], 
            desc: str = "Scanning", 
            **kwargs) -> List[Any]:
        """
        The Heavy Lifter.
        - task_function: function(target) -> returns Result or None
        - targets: List or Range of inputs
        - desc: Label for the progress bar
        """
        
        # Convert range/generator to list so we know the total size for the progress bar
        target_list = list(targets)
        total_targets = len(target_list)
        results = []

        logger.info(f"🚀 {desc}: Processing {total_targets} targets with {config.THREADS} threads...")

        try:
            with ThreadPoolExecutor(max_workers=config.THREADS) as executor:
                # Map futures to targets
                # We pass **kwargs to the function if needed (e.g. url=...)
                future_to_target = {
                    executor.submit(task_function, target, **kwargs): target 
                    for target in target_list
                }

                # 📊 Progress Bar Logic
                if HAS_TQDM:
                    # The "Pro" look
                    futures_iter = tqdm(as_completed(future_to_target), 
                                      total=total_targets, 
                                      desc=desc, 
                                      unit="req", 
                                      leave=False) # Clears bar when done
                else:
                    # The "Basic" look (fallback)
                    futures_iter = as_completed(future_to_target)

                # Collect Results
                for future in futures_iter:
                    try:
                        data = future.result()
                        if data:
                            results.append(data)
                            # If using tqdm, we can write to side without breaking the bar
                            if HAS_TQDM:
                                tqdm.write(f"✅ Hit: {data}")
                                 
                            # ———— SANCHEZ GOLDEN GOAL LOGIC ————
                            if config.STOP_ON_SUCCESS:
                                logger.success("🏆 Golden Goal! Stopping match early.")
                                executor.shutdown(wait=False) # Kill pending threads
                                # Cancel remaining futures to stop them processing
                                for f in future_to_target:
                                    f.cancel()
                                return results # Return immediately with the win
                            # ———————————————————————————————————
                    except KeyboardInterrupt:
                        logger.critical("🛑 Scan cancelled by user.")
                        executor.shutdown(wait=False)
                        break
                    except Exception as e:
                        # Log error but keep moving (don't crash the whole scan)
                        # logger.debug(f"Task failed: {e}") 
                        pass
        
        except KeyboardInterrupt:
            logger.critical("\n🛑 Aborted.")
            return results

        logger.info(f"🏁 Job '{desc}' finished. Found {len(results)} hits.")
        return results

# Singleton instance
engine = Engine()