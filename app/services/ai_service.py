import openai
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import asyncio

from app.core.config import settings


class AIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.conversations = {}  # In-memory storage for demo
        
    async def generate_response(
        self, 
        message: str, 
        user_id: str = "anonymous",
        conversation_id: Optional[str] = None
    ) -> Dict:
        """Generate AI response with context awareness"""
        
        # Create or get conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "user_id": user_id,
                "created_at": datetime.now()
            }
        
        # Add user message to conversation
        self.conversations[conversation_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # Build context from conversation history
        messages = self._build_context(conversation_id)
        
        try:
            # Generate response using OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                stream=False
            )
            
            ai_response = response.choices[0].message.content
            
            # Store AI response
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant", 
                "content": ai_response,
                "timestamp": datetime.now()
            })
            
            return {
                "response": ai_response,
                "conversation_id": conversation_id,
                "sources": []  # For future RAG implementation
            }
            
        except Exception as e:
            # Fallback response
            fallback_response = self._get_fallback_response(message)
            
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": fallback_response,
                "timestamp": datetime.now()
            })
            
            return {
                "response": fallback_response,
                "conversation_id": conversation_id,
                "sources": []
            }
    
    def _build_context(self, conversation_id: str) -> List[Dict]:
        """Build context for AI from conversation history"""
        
        system_prompt = {
            "role": "system",
            "content": """Eres un asistente virtual profesional para un negocio de limpieza profesional llamado 'Rize Professional Cleaning'. 

Información sobre la empresa:
- Servicios: Limpieza residencial, comercial, post-construcción, y mantenimiento
- Horarios: Lunes a Viernes 8:00 AM - 6:00 PM, Sábados 9:00 AM - 3:00 PM
- Contacto: Disponible para cotizaciones gratuitas
- Especialidades: Limpieza profunda, desinfección, limpieza ecológica

Instrucciones:
- Responde de manera profesional y amigable
- Proporciona información útil sobre servicios de limpieza
- Si no tienes información específica, ofrece contactar para más detalles
- Mantén las respuestas concisas pero informativas
- Siempre enfócate en ayudar al cliente"""
        }
        
        messages = [system_prompt]
        
        # Add recent conversation history (last 10 messages)
        if conversation_id in self.conversations:
            recent_messages = self.conversations[conversation_id]["messages"][-10:]
            for msg in recent_messages:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return messages
    
    def _get_fallback_response(self, message: str) -> str:
        """Provide fallback responses when AI is unavailable"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hola", "hello", "hi", "buenos"]):
            return "¡Hola! Soy el asistente virtual de Rize Professional Cleaning. ¿En qué puedo ayudarte hoy?"
        
        elif any(word in message_lower for word in ["precio", "costo", "tarifa", "price"]):
            return "Nuestros precios varían según el tipo y tamaño del servicio. ¿Podrías contarme más sobre lo que necesitas? Ofrecemos cotizaciones gratuitas."
        
        elif any(word in message_lower for word in ["servicio", "limpieza", "service", "cleaning"]):
            return "Ofrecemos servicios de limpieza residencial, comercial, post-construcción y mantenimiento. ¿Qué tipo de servicio te interesa?"
        
        elif any(word in message_lower for word in ["horario", "hora", "schedule", "time"]):
            return "Nuestros horarios son: Lunes a Viernes de 8:00 AM a 6:00 PM, Sábados de 9:00 AM a 3:00 PM. ¿En qué horario te gustaría agendar?"
        
        elif any(word in message_lower for word in ["contacto", "teléfono", "contact", "phone"]):
            return "Puedes contactarnos para una cotización gratuita. ¿Te gustaría que te ayude a programar una consulta?"
        
        else:
            return "Gracias por tu consulta. Soy el asistente de Rize Professional Cleaning. ¿Podrías ser más específico sobre cómo puedo ayudarte con nuestros servicios de limpieza?"