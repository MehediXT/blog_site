import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import UserProfile, ScholarProfile
from fatwas.models import (
    Category,
    Methodology,
    Answer,
    AnswerRevision,
    ReviewDecision,
    Publication,
    Bookmark,
    Report,
)
from questions.models import Question, ClarificationMessage
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Populates the database with realistic dummy data for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting dummy data seeding...'))
        now = timezone.now()

        # ----------------------------------------------------
        # 1. Categories
        # ----------------------------------------------------
        categories_data = [
            {'slug': 'taharah', 'name_en': 'Purity & Cleanliness', 'name_bn': 'পবিত্রতা ও তাহারাত'},
            {'slug': 'salah', 'name_en': 'Prayer (Salah)', 'name_bn': 'সালাত ও নামাজ'},
            {'slug': 'sawm', 'name_en': 'Fasting & Ramadan', 'name_bn': 'সিয়াম ও রোজা'},
            {'slug': 'zakat', 'name_en': 'Zakat & Charity', 'name_bn': 'যাকাত ও সাদাকাহ'},
            {'slug': 'marriage-family', 'name_en': 'Marriage & Family', 'name_bn': 'বিবাহ ও পরিবার'},
            {'slug': 'finance', 'name_en': 'Islamic Finance & Transactions', 'name_bn': 'ইসলামী অর্থনীতি ও লেনদেন'},
            {'slug': 'contemporary', 'name_en': 'Contemporary Issues', 'name_bn': 'সমকালীন আধুনিক বিষয়াবলী'},
        ]
        categories = {}
        for item in categories_data:
            cat, created = Category.objects.update_or_create(
                slug=item['slug'],
                defaults={'name_en': item['name_en'], 'name_bn': item['name_bn'], 'is_active': True},
            )
            categories[item['slug']] = cat
        self.stdout.write(self.style.SUCCESS(f'Populated {len(categories)} categories.'))

        # ----------------------------------------------------
        # 2. Methodologies
        # ----------------------------------------------------
        methodologies_data = [
            {'slug': 'hanafi', 'name_en': 'Hanafi', 'name_bn': 'হানাফী', 'description': 'According to the Hanafi school of jurisprudence.'},
            {'slug': 'shafii', 'name_en': "Shafi'i", 'name_bn': 'শাফেঈ', 'description': "According to the Shafi'i school of jurisprudence."},
            {'slug': 'maliki', 'name_en': 'Maliki', 'name_bn': 'মালিকী', 'description': 'According to the Maliki school of jurisprudence.'},
            {'slug': 'hanbali', 'name_en': 'Hanbali', 'name_bn': 'হাম্বলী', 'description': 'According to the Hanbali school of jurisprudence.'},
            {'slug': 'majority', 'name_en': 'Majority (Jumhur)', 'name_bn': 'জমহুর / সাধারণ ঐক্যমত', 'description': 'Consensus and majority view of classical Islamic scholars.'},
        ]
        methodologies = {}
        for item in methodologies_data:
            meth, created = Methodology.objects.update_or_create(
                slug=item['slug'],
                defaults={'name_en': item['name_en'], 'name_bn': item['name_bn'], 'description': item['description'], 'is_active': True},
            )
            methodologies[item['slug']] = meth
        self.stdout.write(self.style.SUCCESS(f'Populated {len(methodologies)} methodologies.'))

        # ----------------------------------------------------
        # 3. Users (Moderator, Scholars, Question Askers)
        # ----------------------------------------------------
        common_password = 'Password123!'

        # Ensure existing superuser has profile
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            profile, _ = UserProfile.objects.get_or_create(user=superuser)
            profile.display_name = profile.display_name or 'Mehedi (Admin)'
            profile.email_verified = True
            profile.save()

        # Scholars
        scholars_info = [
            {
                'username': 'dr_abdullah',
                'email': 'abdullah@ilm.example.com',
                'display_name': 'Dr. Abdullah Al-Mansoor',
                'language': 'en',
                'status': 'approved',
                'institution': 'Al-Azhar University Graduate, Faculty of Shariah',
                'qualifications': 'PhD in Islamic Jurisprudence (Fiqh & Usul al-Fiqh)',
                'specialties': ['Fiqh', 'Islamic Finance', 'Family Law'],
                'languages': ['en', 'ar', 'bn'],
                'bio': 'Specialist in contemporary financial transactions and classical Hanafi jurisprudence.',
                'public_bio': 'Senior Researcher and Professor of Islamic Jurisprudence.',
            },
            {
                'username': 'mufti_farhan',
                'email': 'farhan@ilm.example.com',
                'display_name': 'Mufti Farhan Ahmed',
                'language': 'bn',
                'status': 'approved',
                'institution': 'Darul Uloom Islamic Academy',
                'qualifications': 'Takhassus fi al-Ifta (Specialization in Islamic Legal Rulings)',
                'specialties': ['Taharah', 'Salah', 'Fasting & Ramadan', 'Contemporary Fiqh'],
                'languages': ['bn', 'en', 'ar'],
                'bio': 'Mufti actively serving the community with daily practical fatwa guidance.',
                'public_bio': 'Senior Mufti and teacher of Hadith and Fiqh.',
            },
            {
                'username': 'ustadh_tariq',
                'email': 'tariq@ilm.example.com',
                'display_name': 'Ustadh Tariq Jameel',
                'language': 'en',
                'status': 'approved',
                'institution': 'International Islamic University',
                'qualifications': 'MA in Islamic Studies & Comparative Religion',
                'specialties': ['Comparative Fiqh', 'Biomedical Ethics', 'Marriage'],
                'languages': ['en', 'ar'],
                'bio': 'Scholar and reviewer focused on cross-madhhab consensus and medical ethics.',
                'public_bio': 'Lecturer and senior fatwa peer reviewer.',
            },
            {
                'username': 'imam_hasan',
                'email': 'hasan@ilm.example.com',
                'display_name': 'Imam Hasan Mahmud',
                'language': 'bn',
                'status': 'pending',
                'institution': 'Jamia Islamia',
                'qualifications': 'Dawra-e Hadith (Masters in Hadith Studies)',
                'specialties': ['Quranic Exegesis', 'Youth Counseling'],
                'languages': ['bn', 'en'],
                'bio': 'Imam and lecturer applying for scholar verification status.',
                'public_bio': 'Community Imam and teacher of Quran and Sunnah.',
            },
        ]

        scholars = {}
        for info in scholars_info:
            u, created = User.objects.get_or_create(
                username=info['username'],
                defaults={'email': info['email'], 'is_staff': False},
            )
            if created or not u.has_usable_password():
                u.set_password(common_password)
                u.save()

            u_prof, _ = UserProfile.objects.get_or_create(user=u)
            u_prof.display_name = info['display_name']
            u_prof.preferred_language = info['language']
            u_prof.email_verified = True
            u_prof.save()

            s_prof, _ = ScholarProfile.objects.get_or_create(user=u)
            s_prof.institution = info['institution']
            s_prof.qualifications = info['qualifications']
            s_prof.specialties = info['specialties']
            s_prof.supported_languages = info['languages']
            s_prof.biography = info['bio']
            s_prof.public_bio = info['public_bio']
            s_prof.verification_status = info['status']
            if info['status'] == 'approved':
                s_prof.verified_at = now - timedelta(days=60)
                if superuser:
                    s_prof.verified_by = superuser
            s_prof.save()
            scholars[info['username']] = u

        # Regular Users (Askers)
        users_info = [
            {'username': 'rahim_user', 'email': 'rahim@example.com', 'display_name': 'Rahim Chowdhury', 'lang': 'bn'},
            {'username': 'ayesha_user', 'email': 'ayesha@example.com', 'display_name': 'Ayesha Siddiqa', 'lang': 'en'},
            {'username': 'karim_user', 'email': 'karim@example.com', 'display_name': 'Karim Uddin', 'lang': 'bn'},
        ]
        users = {}
        for info in users_info:
            u, created = User.objects.get_or_create(
                username=info['username'],
                defaults={'email': info['email']},
            )
            if created or not u.has_usable_password():
                u.set_password(common_password)
                u.save()

            u_prof, _ = UserProfile.objects.get_or_create(user=u)
            u_prof.display_name = info['display_name']
            u_prof.preferred_language = info['lang']
            u_prof.email_verified = True
            u_prof.save()
            users[info['username']] = u

        self.stdout.write(self.style.SUCCESS(f'Populated users and scholars (password: {common_password}).'))

        # ----------------------------------------------------
        # 4. Published Fatwas & Questions
        # ----------------------------------------------------
        fatwas_data = [
            {
                'slug': 'prayer-in-airplane-long-flight-ruling',
                'language': 'en',
                'category': categories['salah'],
                'methodology': methodologies['hanafi'],
                'scholar': scholars['dr_abdullah'],
                'reviewer': scholars['ustadh_tariq'],
                'asker': users['ayesha_user'],
                'original_title': 'How should I perform my prayers when traveling on an 8-hour flight without stopping?',
                'original_body': 'I will be traveling on an international flight that spans the times of Dhuhr, Asr, and Maghrib. Is it permissible to pray while seated in my airplane seat, or must I stand? Also how do I face the Qiblah?',
                'public_title': 'Rulings on Performing Salah While Traveling on an Airplane',
                'public_body': 'What is the correct manner of performing obligatory prayers during long-distance airplane flights when standing or facing the exact Qiblah direction poses physical difficulty?',
                'answer': (
                    "In the Name of Allah, the Most Merciful, the Most Compassionate.\n\n"
                    "1. Obligation of Prayer on Time:\n"
                    "A traveler must perform the obligatory prayers within their designated time windows. It is not permissible to delay prayers beyond their valid time unless combining them under permissible traveling exemptions (Jam' bayn as-Salatayn).\n\n"
                    "2. Standing (Qiyam) and Facing Qibla:\n"
                    "Standing is an integral pillar (rukn) of obligatory prayers. If it is feasible and safe to pray standing without obstructing pathways or endangering safety, the passenger must stand and make an earnest effort to face the Qiblah direction at the commencement of the prayer.\n\n"
                    "3. Praying while Seated:\n"
                    "If the airline crew disallows standing or there is turbulence, severe congestion, or risk of falling, one is permitted to pray seated in their seat with bowing (Ruku) and prostration (Sujud) performed through gestures (Isha'ah), making the prostration lower than the bowing.\n\n"
                    "4. Purity (Taharah):\n"
                    "Wudu should be performed using the plane's lavatory. If water is strictly unavailable or cannot be used, Tayammum on a natural stone surface or dust is permitted.\n\n"
                    "And Allah Knows Best."
                ),
                'references': [
                    'Sahih al-Bukhari, Hadith 1117 (Book of Shortening the Prayers)',
                    'Al-Fatawa al-Hindiyyah, Vol. 1, p. 143',
                    'Fatawa Darul Uloom Deoband, Vol. 4',
                ],
                'days_ago': 12,
            },
            {
                'slug': 'using-asthma-inhaler-during-ramadan-fasting',
                'language': 'bn',
                'category': categories['sawm'],
                'methodology': methodologies['majority'],
                'scholar': scholars['mufti_farhan'],
                'reviewer': scholars['dr_abdullah'],
                'asker': users['rahim_user'],
                'original_title': 'রোজা থাকা অবস্থায় হাঁপানির ইনহেলার ব্যবহার করলে রোজা ভেঙে যাবে কি না?',
                'original_body': 'আমার তীব্র শ্বাসকষ্ট রয়েছে। দিনে এক-দুই বার ইনহেলার স্প্রে নিতে হয়। রমজান মাসে রোজা রেখে ইনহেলার ব্যবহার করলে কি রোজা বাতিল হয়ে যাবে?',
                'public_title': 'রোজা অবস্থায় হাঁপানির ইনহেলার ব্যবহারের বিধান',
                'public_body': 'শ্বাসকষ্টের রোগী রোজা রেখে দিনের বেলায় প্রয়োজনে ইনহেলার স্প্রে ব্যবহার করলে রোজার ওপর এর কী প্রভাব পড়বে?',
                'answer': (
                    "বিসমিল্লাহির রাহমানির রাহিম।\n\n"
                    "হাঁপানির ইনহেলার ব্যবহারে রোজার বিধান নিয়ে সমকালীন ফুকাহায়ে কেরামের মাঝে দুটি প্রধান অভিমত রয়েছে:\n\n"
                    "১. জমহুর ফিকহ একাডেমিসমূহের সিদ্ধান্ত (ইসলামিক ফিকহ একাডেমি, জেদ্দা ও সৌদি স্থায়ী ফতোয়া কমিটি):\n"
                    "ইনহেলারে ব্যবহৃত গ্যাস বা বাষ্প ফুসফুসের শ্বাসনালীকে প্রসারিত করে, এটি খাদ্য বা পানীয় হিসেবে পেটে প্রবেশ করে না এবং এতে দেহের কোনো পুষ্টি সাধিত হয় না। সুতরাং একান্ত প্রয়োজনে ইনহেলার ব্যবহার করলে রোজা নষ্ট হবে না।\n\n"
                    "২. সতর্কতা ও কাজা করার অভিমত (হানাফী ফিকহ অনুযায়ী):\n"
                    "যেহেতু ইনহেলারের সাথে সূক্ষ্ম তরল কণা মুখে ও গলায় প্রবেশ করে, তাই সুস্থ হলে পরবর্তীতে এই রোজার কাজা আদায় করে নেওয়া অধিকতর সতর্কতামূলক। তবে রোগী যদি সার্বক্ষণিক এমন রোগে ভোগেন যার আরোগ্য লাভের আশা নেই, তবে তিনি প্রতি রোজার জন্য ফিদইয়া প্রদান করবেন।\n\n"
                    "পরামর্শ:\n"
                    "যদি সেহরির পূর্বে দীর্ঘস্থায়ী অ্যাকশনযুক্ত ইনহেলার বা ওষুধ গ্রহণ করে দিনের বেলা ইনহেলার গ্রহণ ছাড়া থাকা সম্ভব হয়, তবে সেটাই উত্তম। অন্যথায় স্বাস্থ্যের ক্ষতি না করে ইনহেলার গ্রহণ করবেন।\n\n"
                    "আল্লাহ তাআলাই সর্বাধিক জ্ঞাত।"
                ),
                'references': [
                    'মাজাল্লাত মাজমা আল-ফিকহ আল-ইসলামি (জেদ্দা), রেজুল্যুশন নং ৯৩ (১/১০)',
                    'ফাতাওয়া উসমানী, খণ্ড ২, পৃষ্ঠা ১৮৬',
                    'আল-ফিকহুল ইসলামী ওয়া আদিল্লাতুহু, খণ্ড ৩',
                ],
                'days_ago': 9,
            },
            {
                'slug': 'halal-investing-in-index-funds-and-stocks',
                'language': 'en',
                'category': categories['finance'],
                'methodology': methodologies['majority'],
                'scholar': scholars['dr_abdullah'],
                'reviewer': scholars['ustadh_tariq'],
                'asker': users['karim_user'],
                'original_title': 'Is it permissible to invest in stock market index funds and tech companies?',
                'original_body': 'I work as a software engineer and have savings. Can I invest in US index funds or tech stocks like Apple and Microsoft? What are the conditions for Islamic stock screening?',
                'public_title': 'Criteria for Shariah-Compliant Investment in Stocks and ETFs',
                'public_body': 'What are the required financial screens and Islamic criteria for purchasing shares of publicly listed companies and exchange-traded funds (ETFs)?',
                'answer': (
                    "In the Name of Allah, the Most Merciful, the Most Compassionate.\n\n"
                    "Investing in equities (shares) is fundamentally permissible provided the company complies with Shariah screening standards outlined by international bodies such as AAOIFI:\n\n"
                    "1. Core Business Activity Screen:\n"
                    "The company's primary business must not involve impermissible (Haram) products or services such as conventional banking/interest, alcohol, gambling, adult entertainment, pork, or weapons of unlawful warfare.\n\n"
                    "2. Financial Ratio Screens:\n"
                    "- Total interest-bearing debt divided by market capitalization should typically not exceed 33%.\n"
                    "- Cash and interest-bearing securities divided by market capitalization should not exceed 33%.\n"
                    "- Impermissible secondary revenue must be less than 5% of total gross revenue.\n\n"
                    "3. Dividend Purification:\n"
                    "If a permissible company earns a small percentage of interest on bank deposits (under 5%), that exact percentage of the dividend payout must be purified by donating it to charity without expecting spiritual reward.\n\n"
                    "Conclusion: Investing in certified Shariah-screened funds or individual stocks that meet these parameters is permissible.\n\n"
                    "And Allah Knows Best."
                ),
                'references': [
                    'AAOIFI Shariah Standard No. 21 (Financial Papers / Shares and Bonds)',
                    'Fiqh of Financial Transactions by Mufti Taqi Usmani',
                    'Resolutions of the International Islamic Fiqh Academy on Stock Markets',
                ],
                'days_ago': 6,
            },
            {
                'slug': 'wiping-over-socks-masah-khuffayn-rules',
                'language': 'bn',
                'category': categories['taharah'],
                'methodology': methodologies['hanafi'],
                'scholar': scholars['mufti_farhan'],
                'reviewer': scholars['ustadh_tariq'],
                'asker': users['rahim_user'],
                'original_title': 'শীতকালে সাধারণ সুতি মোজার ওপর মাসেহ করা যাবে কি?',
                'original_body': 'অফিসে বা শীতে ওজু করার সময় চামড়ার মোজা ছাড়া সাধারণ সুতি বা উলের কাপড়ের মোজার ওপর হাত ভেজা দিয়ে মাসেহ করা জায়েজ কি না?',
                'public_title': 'সাধারণ মোজার ওপর মাসেহ করার শরয়ী বিধান',
                'public_body': 'চামড়ার তৈরি খাফফাইন ছাড়া বর্তমান যুগের প্রচলিত সুতি বা সিন্থেটিক কাপড়ের মোজার ওপর অজুতে মাসেহ করার শর্তাবলি কী?',
                'answer': (
                    "বিসমিল্লাহির রাহমানির রাহিম।\n\n"
                    "অজুতে পায়ের মোজার ওপর মাসেহ করার বিধান:\n\n"
                    "১. চামড়ার মোজা (খুফফাইন):\n"
                    "পবিত্র অবস্থায় ওজু পূর্ণ করে চামড়ার মোজা পরিধান করলে মুকিম ব্যক্তির জন্য ১ দিন ১ রাত (২৪ ঘণ্টা) এবং মুসাফিরের জন্য ৩ দিন ৩ রাত (৭২ ঘণ্টা) অজু ভঙ্গের পর নতুন ওজুতে মোজা না খুলে এর ওপর মাসেহ করা সর্বসম্মতভাবে জায়েজ।\n\n"
                    "২. সাধারণ কাপড়ের মোজা (সুতি/নাইলন):\n"
                    "প্রচলিত পাতলা সুতি বা নাইলনের মোজার ওপর হানাফী মাজহাবের মূল ফতোয়া অনুযায়ী মাসেহ বৈধ নয়। সাধারণ মোজায় মাসেহ জায়েজ হতে হলে তিনটি শর্ত পূরণ করতে হবে:\n"
                    "- মোজাটি এমন পুরু হতে হবে যেন পানি ভেতরে সরাসরি ত্বক পর্যন্ত না পৌঁছে।\n"
                    "- ফিতা বা কোনো কিছু দিয়ে না বেঁধে মোজা নিজে নিজেই পায়ের গোড়ালির ওপর দাঁড়িয়ে থাকে।\n"
                    "- মোজা পরে অন্তত ৩ মাইল হেঁটে যাওয়া সম্ভব এবং তা ছিঁড়ে না যায়।\n\n"
                    "যেহেতু সাধারণ পাতলা মোজায় এই শর্তগুলো পাওয়া যায় না, তাই পাতলা সুতি মোজা খুলে পা ধৌত করাই আবশ্যক। তবে বিশেষ ওয়াটারপ্রুফ ঘন মোজায় শর্ত পূরণ হলে মাসেহ বৈধ।\n\n"
                    "আল্লাহ তাআলাই সর্বাধিক জ্ঞাত।"
                ),
                'references': [
                    'বাদায়েউস সানায়ে, খণ্ড ১, পৃষ্ঠা ১০',
                    'রদ্দুল মুহতার (ফাতওয়ায়ে শামী), খণ্ড ১, পৃষ্ঠা ২৬৯',
                    'সহীহ মুসলিম, হাদিস নং ২৭৬',
                ],
                'days_ago': 3,
            },
            {
                'slug': 'mahr-prompt-deferred-conditions-in-nikah',
                'language': 'en',
                'category': categories['marriage-family'],
                'methodology': methodologies['hanafi'],
                'scholar': scholars['dr_abdullah'],
                'reviewer': scholars['mufti_farhan'],
                'asker': users['ayesha_user'],
                'original_title': 'Is it required to pay the full Mahr immediately upon marriage?',
                'original_body': 'During the Nikah contract, can the Mahr be split into an immediate amount and a deferred amount? What happens if the deferred amount is not paid?',
                'public_title': 'Rules Regarding Prompt (Muajjal) and Deferred (Muwajjal) Mahr',
                'public_body': 'What is the Islamic validity and legal conditions of dividing dowry (Mahr) into immediate and delayed payments at the time of marriage?',
                'answer': (
                    "In the Name of Allah, the Most Merciful, the Most Compassionate.\n\n"
                    "Mahr (dowry) is a mandatory gift given by the groom to the bride in honor of the marriage contract. The Shariah provides flexibility in how it is scheduled:\n\n"
                    "1. Prompt (Mu'ajjal) vs Deferred (Mu'wajjal):\n"
                    "It is fully valid by agreement of both parties to stipulate part of the Mahr as prompt (payable immediately prior to or upon consummation) and part as deferred (payable at an agreed future date, or upon death/divorce).\n\n"
                    "2. Rights of the Wife:\n"
                    "The wife has the full legal right to withhold intimacy until the prompt portion of the Mahr agreed upon is handed over to her.\n\n"
                    "3. Nature of Deferred Mahr:\n"
                    "Deferred Mahr constitutes an outstanding debt upon the husband. It must be paid according to the terms agreed upon. Intentionally withholding it without the wife's voluntary waiver is a grave sin.\n\n"
                    "And Allah Knows Best."
                ),
                'references': [
                    'Surah An-Nisa, 4:4 ("And give women their dowries as a free gift...")',
                    'Al-Hidayah, Kitab an-Nikah (Chapter on Mahr)',
                    'Fatawa Hindiyyah, Vol. 1, p. 303',
                ],
                'days_ago': 1,
            },
        ]

        for item in fatwas_data:
            q_time = now - timedelta(days=item['days_ago'] + 2)
            pub_time = now - timedelta(days=item['days_ago'])

            q = Question.objects.create(
                owner=item['asker'],
                original_title=item['original_title'],
                original_body=item['original_body'],
                public_title=item['public_title'],
                public_body=item['public_body'],
                language=item['language'],
                category=item['category'],
                status='answered',
                is_public=True,
                assigned_scholar=item['scholar'],
                assigned_reviewer=item['reviewer'],
                submitted_at=q_time,
                assigned_at=q_time + timedelta(hours=6),
            )

            ans = Answer.objects.create(
                question=q,
                author=item['scholar'],
            )

            rev = AnswerRevision.objects.create(
                answer=ans,
                revision_number=1,
                language=item['language'],
                body=item['answer'],
                public_question_title=item['public_title'],
                public_question_body=item['public_body'],
                references=item['references'],
                methodology=item['methodology'],
                status='approved',
                created_by=item['scholar'],
                submitted_at=pub_time - timedelta(hours=5),
            )

            ans.approved_revision = rev
            ans.save()

            ReviewDecision.objects.create(
                revision=rev,
                reviewer=item['reviewer'],
                decision='approved',
                feedback='Meticulous research with clear classical references. Approved for public dissemination.',
            )

            pub, _ = Publication.objects.get_or_create(
                slug=item['slug'],
                defaults={
                    'answer': ans,
                    'approved_revision': rev,
                    'public_id': uuid.uuid4(),
                    'visibility': 'public',
                    'published_at': pub_time,
                },
            )

            # Add bookmarks
            Bookmark.objects.get_or_create(user=users['rahim_user'], publication=pub)
            if item['language'] == 'en':
                Bookmark.objects.get_or_create(user=users['ayesha_user'], publication=pub)

        self.stdout.write(self.style.SUCCESS('Created 5 published fatwas with revisions, decisions, and bookmarks.'))

        # ----------------------------------------------------
        # 5. In-Progress & Pending Questions (Workflow Testing)
        # ----------------------------------------------------

        # Question A: Needs Clarification
        q_clarif = Question.objects.create(
            owner=users['rahim_user'],
            original_title='ব্যাংক থেকে বাড়ি ক্রয়ের জন্য হোম লোন নেওয়ার বিধান কি?',
            original_body='আমি একটি ফ্ল্যাট কিনতে চাই। প্রচলিত ব্যাংকের হাউজিং লোন এবং ইসলামিক ব্যাংকের হোম ফাইন্যান্সিংয়ের মধ্যে পার্থক্য কি?',
            public_title='',
            public_body='',
            language='bn',
            category=categories['finance'],
            status='needs_clarification',
            is_public=False,
            assigned_scholar=scholars['dr_abdullah'],
            assigned_reviewer=scholars['ustadh_tariq'],
            submitted_at=now - timedelta(days=2),
            assigned_at=now - timedelta(days=1),
        )
        ClarificationMessage.objects.create(
            question=q_clarif,
            author=scholars['dr_abdullah'],
            body='অনুগ্রহ করে জানান আপনি যে ইসলামিক ব্যাংক থেকে ঋণ নেওয়ার কথা ভাবছেন তাদের চুক্তির ধরন কী? এটি কি মুরাবাহা নাকি মুশারাকা মুতানাখিসাহ?',
        )
        ClarificationMessage.objects.create(
            question=q_clarif,
            author=users['rahim_user'],
            body='ব্যাংক কর্মকর্তা জানিয়েছেন এটি ডিমিনিশিং মুশারাকা (মুশারাকা মুতানাখিসাহ) ভিত্তিক চুক্তি।',
        )

        # Question B: Assigned (Scholar drafting answer)
        Question.objects.create(
            owner=users['ayesha_user'],
            original_title='Rules of combining prayers during severe rain and thunderstorms',
            original_body='Is it allowed for an individual praying at home to combine Maghrib and Isha during torrential rain, or is that dispensation strictly for congregation in the mosque?',
            public_title='Combining Prayers at Home Due to Heavy Rain and Storms',
            public_body='Can someone praying alone at home combine Maghrib and Isha due to extreme rainstorms?',
            language='en',
            category=categories['salah'],
            status='assigned',
            is_public=True,
            assigned_scholar=scholars['dr_abdullah'],
            assigned_reviewer=scholars['ustadh_tariq'],
            submitted_at=now - timedelta(days=1),
            assigned_at=now - timedelta(hours=10),
        )

        # Question C: Submitted (Awaiting moderation / scholar assignment)
        Question.objects.create(
            owner=users['karim_user'],
            original_title='রমজানের শেষ দশকে ইতিকাফের শর্তাবলি এবং মহিলারা ঘরে ইতিকাফ করতে পারবেন কি?',
            original_body='মহিলারা কীভাবে ঘরে ইতিকাফ করবেন এবং এর নিয়ম ও শর্তগুলো জানতে চাই।',
            public_title='মহিলাদের ঘরে ইতিকাফের বিধান ও শর্তাবলি',
            public_body='মহিলাদের নিজ বাসগৃহের নির্দিষ্ট স্থানে ইতিকাফ পালনের নিয়ম ও করণীয়।',
            language='bn',
            category=categories['sawm'],
            status='submitted',
            is_public=True,
            submitted_at=now - timedelta(hours=4),
        )

        self.stdout.write(self.style.SUCCESS('Created workflow test questions (needs_clarification, assigned, submitted).'))

        # ----------------------------------------------------
        # 6. Sample Report & Notifications
        # ----------------------------------------------------
        first_pub = Publication.objects.filter(visibility='public').first()
        if first_pub:
            Report.objects.get_or_create(
                publication=first_pub,
                reporter=users['karim_user'],
                defaults={
                    'reason': 'Formatting typo in citation number 2.',
                    'status': 'open',
                },
            )

        # Sample notifications
        Notification.objects.create(
            user=users['ayesha_user'],
            kind='question_answered',
            title='Your question has been answered!',
            body='Your question regarding airplane prayer rulings has been approved and published.',
            target_url=f'/en/fatwas/{first_pub.id}' if first_pub else '',
        )
        Notification.objects.create(
            user=users['rahim_user'],
            kind='clarification_requested',
            title='Clarification requested on your question',
            body='Dr. Abdullah has requested additional details about your home loan inquiry.',
            target_url=f'/bn/account',
        )

        self.stdout.write(self.style.SUCCESS('Created sample notifications and report.'))
        self.stdout.write(self.style.SUCCESS('\n=== Dummy Data Seeding Successfully Completed! ===\n'))
