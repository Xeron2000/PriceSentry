"""
Tests for utils/get_exchange.py - Exchange factory functionality.
"""

import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.get_exchange import get_exchange


class TestGetExchange:
    """Test cases for get_exchange function."""

    def test_get_exchange_binance(self):
        """Test getting Binance exchange instance."""
        with patch('exchanges.BinanceExchange') as mock_binance:
            mock_instance = Mock()
            mock_binance.return_value = mock_instance
            
            result = get_exchange('binance')
            
            assert result == mock_instance
            mock_binance.assert_called_once()

    def test_get_exchange_binance_uppercase(self):
        """Test getting Binance exchange with uppercase name."""
        with patch('exchanges.BinanceExchange') as mock_binance:
            mock_instance = Mock()
            mock_binance.return_value = mock_instance
            
            result = get_exchange('BINANCE')
            
            assert result == mock_instance
            mock_binance.assert_called_once()

    def test_get_exchange_binance_mixed_case(self):
        """Test getting Binance exchange with mixed case name."""
        with patch('exchanges.BinanceExchange') as mock_binance:
            mock_instance = Mock()
            mock_binance.return_value = mock_instance
            
            result = get_exchange('Binance')
            
            assert result == mock_instance
            mock_binance.assert_called_once()

    def test_get_exchange_okx(self):
        """Test getting OKX exchange instance."""
        with patch('exchanges.OkxExchange') as mock_okx:
            mock_instance = Mock()
            mock_okx.return_value = mock_instance
            
            result = get_exchange('okx')
            
            assert result == mock_instance
            mock_okx.assert_called_once()

    def test_get_exchange_okx_uppercase(self):
        """Test getting OKX exchange with uppercase name."""
        with patch('exchanges.OkxExchange') as mock_okx:
            mock_instance = Mock()
            mock_okx.return_value = mock_instance
            
            result = get_exchange('OKX')
            
            assert result == mock_instance
            mock_okx.assert_called_once()

    def test_get_exchange_bybit(self):
        """Test getting Bybit exchange instance."""
        with patch('exchanges.BybitExchange') as mock_bybit:
            mock_instance = Mock()
            mock_bybit.return_value = mock_instance
            
            result = get_exchange('bybit')
            
            assert result == mock_instance
            mock_bybit.assert_called_once()

    def test_get_exchange_bybit_uppercase(self):
        """Test getting Bybit exchange with uppercase name."""
        with patch('exchanges.BybitExchange') as mock_bybit:
            mock_instance = Mock()
            mock_bybit.return_value = mock_instance
            
            result = get_exchange('BYBIT')
            
            assert result == mock_instance
            mock_bybit.assert_called_once()

    def test_get_exchange_unsupported(self):
        """Test getting unsupported exchange."""
        with pytest.raises(ValueError, match="Exchange unsupported not supported."):
            get_exchange('unsupported')

    def test_get_exchange_empty_string(self):
        """Test getting exchange with empty string."""
        with pytest.raises(ValueError, match="Exchange  not supported."):
            get_exchange('')

    def test_get_exchange_none(self):
        """Test getting exchange with None."""
        with pytest.raises(ValueError, match="Exchange None not supported."):
            get_exchange(None)

    def test_get_exchange_whitespace(self):
        """Test getting exchange with whitespace."""
        with pytest.raises(ValueError, match="Exchange   not supported."):
            get_exchange('   ')

    def test_get_exchange_partial_match(self):
        """Test getting exchange with partial name match."""
        with pytest.raises(ValueError, match="Exchange bin not supported."):
            get_exchange('bin')

    def test_get_exchange_special_characters(self):
        """Test getting exchange with special characters."""
        with pytest.raises(ValueError, match="Exchange bin@nce not supported."):
            get_exchange('bin@nce')

    def test_get_exchange_numbers(self):
        """Test getting exchange with numbers."""
        with pytest.raises(ValueError, match="Exchange 123 not supported."):
            get_exchange('123')

    def test_get_exchange_case_insensitive_behavior(self):
        """Test that exchange names are case insensitive."""
        test_cases = [
            ('binance', 'BinanceExchange'),
            ('BINANCE', 'BinanceExchange'),
            ('Binance', 'BinanceExchange'),
            ('okx', 'OkxExchange'),
            ('OKX', 'OkxExchange'),
            ('Okx', 'OkxExchange'),
            ('bybit', 'BybitExchange'),
            ('BYBIT', 'BybitExchange'),
            ('Bybit', 'BybitExchange'),
        ]
        
        for exchange_name, expected_class in test_cases:
            with patch(f'exchanges.{expected_class}') as mock_class:
                mock_instance = Mock()
                mock_class.return_value = mock_instance
                
                result = get_exchange(exchange_name)
                
                assert result == mock_instance
                mock_class.assert_called_once()

    def test_get_exchange_returns_new_instance(self):
        """Test that each call returns a new instance."""
        with patch('exchanges.BinanceExchange') as mock_binance:
            mock_instance1 = Mock()
            mock_instance2 = Mock()
            mock_binance.side_effect = [mock_instance1, mock_instance2]
            
            result1 = get_exchange('binance')
            result2 = get_exchange('binance')
            
            assert result1 == mock_instance1
            assert result2 == mock_instance2
            assert result1 is not result2
            assert mock_binance.call_count == 2