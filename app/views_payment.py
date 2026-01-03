"""
Payment Tracking Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Payment, Member, MeetingInfo
from .views import context_data
from .audit_logger import audit_log_user_action
from .constants import PAGINATION_MEMBER_LIST
from datetime import datetime, date


@login_required
def payment_list(request):
    """List all payments with filters"""
    context = context_data(request)
    context['page_name'] = 'Payment List'
    
    # Get filters from request
    member_id_filter = request.GET.get('member_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Build query
    payments = Payment.objects.select_related('member', 'meeting', 'created_by').all()
    
    if member_id_filter:
        payments = payments.filter(member__member_id__icontains=member_id_filter)
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Get statistics
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_count = payments.count()
    
    # Pagination
    paginator = Paginator(payments.order_by('-payment_date'), 20)
    page = request.GET.get('page', 1)
    
    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)
    
    context.update({
        'payments': payments_page,
        'page_obj': payments_page,
        'total_amount': total_amount,
        'total_count': total_count,
        'member_id_filter': member_id_filter,
        'date_from': date_from,
        'date_to': date_to,
        'payment_method': payment_method,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'breadcrumb_items': [
            {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
            {'name': 'Payments', 'icon': 'money-bill-wave'},
        ]
    })
    
    return render(request, 'payment/list.html', context)


@login_required
def payment_add(request):
    """Add a new payment"""
    context = context_data(request)
    context['page_name'] = 'Add Payment'
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'CASH')
        meeting_id = request.POST.get('meeting_id', '')
        receipt_number = request.POST.get('receipt_number', '')
        notes = request.POST.get('notes', '')
        
        try:
            member = Member.objects.get(member_id=member_id)
            meeting = None
            if meeting_id:
                meeting = MeetingInfo.objects.get(meeting_id=meeting_id)
            
            payment = Payment.objects.create(
                member=member,
                meeting=meeting,
                amount=amount,
                payment_method=payment_method,
                receipt_number=receipt_number,
                notes=notes,
                created_by=request.user
            )
            
            # Audit log
            audit_log_user_action(
                request=request,
                action='payment_added',
                target=f'payment:{payment.payment_id}',
                extra_details={
                    'member_id': member.member_id,
                    'amount': str(amount),
                    'payment_method': payment_method,
                }
            )
            
            messages.success(request, f'Payment of Rs.{amount} recorded successfully.')
            return redirect('payment_list')
        except Member.DoesNotExist:
            messages.error(request, 'Member not found.')
        except MeetingInfo.DoesNotExist:
            messages.error(request, 'Meeting not found.')
        except Exception as e:
            messages.error(request, f'Error adding payment: {str(e)}')
    
    # Get members and meetings for dropdowns
    members = Member.objects.filter(member_is_active=True).order_by('member_first_name')
    meetings = MeetingInfo.objects.order_by('-meeting_date')[:20]
    
    context.update({
        'members': members,
        'meetings': meetings,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'breadcrumb_items': [
            {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
            {'name': 'Payments', 'url': '/payment/list/', 'icon': 'money-bill-wave'},
            {'name': 'Add Payment', 'icon': 'plus'},
        ]
    })
    
    return render(request, 'payment/add.html', context)


@login_required
def payment_edit(request, payment_id):
    """Edit a payment"""
    context = context_data(request)
    context['page_name'] = 'Edit Payment'
    
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        meeting_id = request.POST.get('meeting_id', '')
        receipt_number = request.POST.get('receipt_number', '')
        notes = request.POST.get('notes', '')
        
        try:
            meeting = None
            if meeting_id:
                meeting = MeetingInfo.objects.get(meeting_id=meeting_id)
            
            payment.amount = amount
            payment.payment_method = payment_method
            payment.meeting = meeting
            payment.receipt_number = receipt_number
            payment.notes = notes
            payment.save()
            
            # Audit log
            audit_log_user_action(
                request=request,
                action='payment_updated',
                target=f'payment:{payment.payment_id}',
                extra_details={
                    'member_id': payment.member.member_id,
                    'amount': str(amount),
                }
            )
            
            messages.success(request, 'Payment updated successfully.')
            return redirect('payment_list')
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
    
    meetings = MeetingInfo.objects.order_by('-meeting_date')[:20]
    
    context.update({
        'payment': payment,
        'meetings': meetings,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'breadcrumb_items': [
            {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
            {'name': 'Payments', 'url': '/payment/list/', 'icon': 'money-bill-wave'},
            {'name': 'Edit Payment', 'icon': 'edit'},
        ]
    })
    
    return render(request, 'payment/edit.html', context)


@user_passes_test(lambda u: u.is_superuser)
def payment_delete(request, payment_id):
    """Delete a payment"""
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    try:
        member_id = payment.member.member_id
        amount = payment.amount
        
        # Audit log
        audit_log_user_action(
            request=request,
            action='payment_deleted',
            target=f'payment:{payment_id}',
            extra_details={
                'member_id': member_id,
                'amount': str(amount),
            }
        )
        
        payment.delete()
        messages.success(request, 'Payment deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting payment: {str(e)}')
    
    return redirect('payment_list')


@login_required
def payment_statistics(request):
    """Payment statistics and analytics"""
    context = context_data(request)
    context['page_name'] = 'Payment Statistics'
    
    # Get date range from request or default to current year
    year = int(request.GET.get('year', datetime.now().year))
    
    # Total statistics
    all_payments = Payment.objects.filter(payment_date__year=year)
    total_amount = all_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_count = all_payments.count()
    
    # By payment method
    by_method = all_payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('payment_id')
    ).order_by('-total')
    
    # Monthly breakdown
    monthly_data = []
    for month in range(1, 13):
        month_payments = all_payments.filter(payment_date__month=month)
        monthly_data.append({
            'month': datetime(year, month, 1).strftime('%B'),
            'amount': month_payments.aggregate(total=Sum('amount'))['total'] or 0,
            'count': month_payments.count()
        })
    
    # Top paying members
    top_members = all_payments.values(
        'member__member_id',
        'member__member_first_name',
        'member__member_last_name'
    ).annotate(
        total=Sum('amount'),
        count=Count('payment_id')
    ).order_by('-total')[:10]
    
    context.update({
        'year': year,
        'total_amount': total_amount,
        'total_count': total_count,
        'by_method': by_method,
        'monthly_data': monthly_data,
        'top_members': top_members,
        'breadcrumb_items': [
            {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
            {'name': 'Payments', 'url': '/payment/list/', 'icon': 'money-bill-wave'},
            {'name': 'Statistics', 'icon': 'chart-bar'},
        ]
    })
    
    return render(request, 'payment/statistics.html', context)

