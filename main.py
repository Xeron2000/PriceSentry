import logging
import time
import sys
import traceback
from utils.loadConfig import loadConfig
from utils.loadSymbolsFromFile import loadSymbolsFromFile
from utils.matchSymbols import matchSymbols
from utils.parseTimeframe import parseTimeframe
from utils.monitorTopMovers import monitorTopMovers
from utils.sendNotifications import sendNotifications
from exchanges.exchanges import Exchange
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level to show more information
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pricesentry.log")  # Add file logging
    ]
)

# Adjust log level for third-party libraries (avoid excessive logs)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

def main():
    try:
        # Load configuration
        config = loadConfig()
        
        # Initialize exchange
        exchange_name = config.get('exchange', 'binance')
        exchange = Exchange(exchange_name)
        
        # Load trading pairs
        symbols_file_path = config.get('symbolsFilePath', 'config/symbols.txt')
        symbols = loadSymbolsFromFile(symbols_file_path)
        
        # Match trading pairs supported by the exchange
        matched_symbols = matchSymbols(symbols, exchange_name)
        
        if not matched_symbols:
            logging.warning("No matched symbols found. Please check your symbols file.")
            return
        
        # Parse default timeframe
        default_timeframe = config.get('defaultTimeframe', '5m')
        minutes = parseTimeframe(default_timeframe)
        
        # Get default threshold
        threshold = config.get('defaultThreshold', 1)
        
        # Start WebSocket connection
        exchange.start_websocket(matched_symbols)
        logging.info(f"Started WebSocket connection for {len(matched_symbols)} symbols")
        
        # Main loop - set check interval based on defaultTimeframe
        # Convert timeframe to seconds as check interval
        check_interval = minutes * 60  # Convert minutes to seconds
        last_check_time = 0
        
        try:
            logging.info("Entering main loop, starting price movement monitoring")
            logging.info(f"Check interval set to {minutes} minutes ({check_interval} seconds)")
            while True:
                current_time = time.time()
                
                # Check price movements every check_interval seconds
                if current_time - last_check_time >= check_interval:
                    logging.info(f"Checking price movements, {int(current_time - last_check_time)} seconds since last check")
                    
                    # Monitor price movements
                    logging.debug(f"Calling monitorTopMovers, timeframe: {minutes} minutes, threshold: {threshold}%")
                    # Original code might be like this
                    message = monitorTopMovers(minutes, matched_symbols, threshold, exchange, config)
                    
                    message = asyncio.run(monitorTopMovers(minutes, matched_symbols, threshold, exchange, config))
                    
                    # If price movements exceed threshold, send notification
                    if message:
                        logging.info(f"Detected price movements exceeding threshold, message content: {message}")
                        notification_channels = config.get('notificationChannels', [])
                        telegram_config = config.get('telegram', {})
                        dingding_config = config.get('dingding', {})
                        
                        logging.debug(f"Sending notifications, channels: {notification_channels}")
                        sendNotifications(
                            message,
                            notification_channels,
                            telegram_config,
                            dingding_config
                        )
                    else:
                        logging.info("No price movements exceeding threshold detected")
                    
                    last_check_time = current_time
                
                # Check WebSocket connection status every minute
                if int(current_time) % 60 == 0:
                    logging.debug("Checking WebSocket connection status")
                    if not exchange.ws_connected:
                        logging.warning("WebSocket connection disconnected, attempting to reconnect")
                        exchange.check_ws_connection()
                    # Print number of cached symbols
                    if hasattr(exchange, 'last_prices'):
                        logging.debug(f"Number of symbols with cached prices: {len(exchange.last_prices)}")
                
                # Sleep for a while to avoid high CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt. Shutting down...")
        finally:
            # Close WebSocket connection
            exchange.close()
            
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        traceback.print_exc()
        
        # Ensure exchange connection is closed
        if 'exchange' in locals():
            exchange.close()

if __name__ == "__main__":
    main()
