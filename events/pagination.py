from rest_framework.pagination import PageNumberPagination

class CustomEventPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow client to specify page size (optional)
    max_page_size = 100  # Limit the maximum page size
