from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.request import Request
from . import processors


    
class BujjiesponseSSEView(APIView):
    
    def post(self, request : Request):
        processor = processors.BujjiConversationResponseProcessor(request=request)
        processor.init_proccessing()
        return StreamingHttpResponse(processor.process_response_with_events(), content_type="text/event-stream")
   