"""
Azure Application Insights Observability Module.

This module sets up comprehensive telemetry, logging, and tracing
using Azure Application Insights and OpenTelemetry, ensuring enterprise-grade
observability for the GenAI Orchestrator.
"""

import os
import logging
from typing import Optional, Any

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

class ObservabilityManager:
    """
    Configures and manages OpenTelemetry instrumentation for Azure Application Insights.
    """

    @staticmethod
    def configure_telemetry(app: Optional[Any] = None) -> None:
        """
        Initializes Azure Monitor OpenTelemetry and instruments core libraries.

        Args:
            app (Optional[Any]): The FastAPI application instance to instrument.
        """
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        
        if not connection_string:
            logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not found. Telemetry is disabled.")
            return

        try:
            # Configure Azure Monitor with OpenTelemetry
            configure_azure_monitor(
                connection_string=connection_string,
                logger_name="EnterpriseGenAI",
            )
            
            # Instrument standard HTTP requests
            RequestsInstrumentor().instrument()
            
            # If a FastAPI app is provided, instrument it
            if app:
                try:
                    FastAPIInstrumentor.instrument_app(app)
                    logger.info("FastAPI successfully instrumented with OpenTelemetry.")
                except Exception as e:
                    logger.warning(f"Failed to instrument FastAPI app: {e}")

            logger.info("Azure Application Insights telemetry configured successfully.")
            
        except Exception as e:
            logger.error(f"Failed to configure Azure Monitor telemetry: {e}", exc_info=True)

    @staticmethod
    def get_tracer(module_name: str) -> trace.Tracer:
        """
        Retrieves an OpenTelemetry tracer for custom span creation.

        Args:
            module_name (str): The name of the module requesting the tracer.

        Returns:
            trace.Tracer: An OpenTelemetry tracer instance.
        """
        return trace.get_tracer(module_name)
