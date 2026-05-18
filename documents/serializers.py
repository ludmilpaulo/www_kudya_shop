# documents/serializers.py
# serializers.py
from rest_framework import serializers
from .models import Document, Signature, SignatureInvite, VerificationDocument

class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    signed_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'signed_file', 'signed_file_url', 'uploaded_by', 'is_signed', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None

    def get_signed_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.signed_file.url) if obj.signed_file else None

class SignatureInviteSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)  # ✅ Nested serializer

    class Meta:
        model = SignatureInvite
        fields = [
            'id', 'document', 'email', 'token', 'signed', 
            'sent_at', 'created_at', 'invited_by'
        ]
        
    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None



class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = '__all__'


class VerificationDocumentSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    reviewer_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)
    country_name = serializers.CharField(source='country.name', read_only=True, allow_null=True)
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = VerificationDocument
        fields = [
            'id',
            'owner',
            'owner_email',
            'subject_type',
            'subject_id',
            'document_type',
            'file',
            'file_url',
            'country',
            'country_name',
            'city',
            'city_name',
            'status',
            'reviewed_by',
            'reviewer_email',
            'reviewed_at',
            'rejection_reason',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'owner',
            'status',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if request and obj.file else None
        
        
