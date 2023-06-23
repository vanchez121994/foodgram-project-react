from rest_framework import pagination


class LimitPageNumberPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
