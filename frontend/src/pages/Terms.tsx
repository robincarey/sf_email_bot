import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

export function TermsContent({ embedded = false }: { embedded?: boolean }) {
  return (
    <div
      className={`max-w-3xl mx-auto text-sm text-text leading-relaxed ${
        embedded ? 'px-0 py-2' : 'px-6 py-12'
      }`}
    >
      <h1 className="text-3xl font-bold text-text mb-2">Terms of Service</h1>
      <p className="text-text-muted mb-10">Last updated March 30, 2026</p>

      <h2 className="text-xl font-bold text-text mt-10 mb-4">Agreement to Our Legal Terms</h2>
      <p className="mb-4">
        We are SFF Stock Alerts ("Company," "we," "us," "our"). We operate the website{" "}
        <a href="https://sffstock.com" className="text-brand underline hover:text-brand-dark">
          https://sffstock.com
        </a>{" "}
        (the "Site"), as well as any other related products and services that refer or link to
        these legal terms (collectively, the "Services").
      </p>
      <p className="mb-4">
        SFF Stock Alerts is a free notification service that monitors special and limited edition
        science fiction and fantasy book retailers for new listings, restocks, and price changes,
        and sends email alerts to subscribed users based on their preferences.
      </p>
      <p className="mb-4">
        You can contact us via the{" "}
        <a href="/app/contact" className="text-brand underline hover:text-brand-dark">
          contact form
        </a>{" "}
        on our website.
      </p>
      <p className="mb-4">
        These Legal Terms constitute a legally binding agreement between you and SFF Stock Alerts
        concerning your access to and use of the Services. By accessing the Services, you have
        read, understood, and agreed to be bound by all of these Legal Terms. IF YOU DO NOT AGREE
        WITH ALL OF THESE LEGAL TERMS, THEN YOU ARE EXPRESSLY PROHIBITED FROM USING THE SERVICES
        AND YOU MUST DISCONTINUE USE IMMEDIATELY.
      </p>
      <p className="mb-4">
        We reserve the right to make changes to these Legal Terms at any time. We will alert you
        about any changes by updating the "Last updated" date. Your continued use of the Services
        after the date such revised Legal Terms are posted constitutes acceptance of those changes.
      </p>
      <p className="mb-10">
        The Services are intended for users who are at least 18 years old. Persons under the age
        of 18 are not permitted to use or register for the Services.
      </p>

      {/* TOC */}
      <h2 className="text-xl font-bold text-text mt-10 mb-4">Table of Contents</h2>
      <ol className="list-decimal pl-6 space-y-1 mb-10">
        {[
          ["#services", "Our Services"],
          ["#ip", "Intellectual Property Rights"],
          ["#userreps", "User Representations"],
          ["#userreg", "User Registration"],
          ["#prohibited", "Prohibited Activities"],
          ["#ugc", "User Generated Contributions"],
          ["#license", "Contribution License"],
          ["#thirdparty", "Third-Party Websites and Content"],
          ["#sitemanage", "Services Management"],
          ["#ppyes", "Privacy Policy"],
          ["#terms", "Term and Termination"],
          ["#modifications", "Modifications and Interruptions"],
          ["#law", "Governing Law"],
          ["#disputes", "Dispute Resolution"],
          ["#corrections", "Corrections"],
          ["#disclaimer", "Disclaimer"],
          ["#liability", "Limitations of Liability"],
          ["#indemnification", "Indemnification"],
          ["#userdata", "User Data"],
          ["#electronic", "Electronic Communications, Transactions, and Signatures"],
          ["#california", "California Users and Residents"],
          ["#misc", "Miscellaneous"],
          ["#contact", "Contact Us"],
        ].map(([href, label], i) => (
          <li key={href}>
            <a href={href} className="text-brand underline hover:text-brand-dark">
              {i + 1}. {label}
            </a>
          </li>
        ))}
      </ol>

      {/* 1 */}
      <h2 id="services" className="text-xl font-bold text-text mt-10 mb-4">1. Our Services</h2>
      <p className="mb-4">
        The information provided when using the Services is not intended for distribution to or
        use by any person or entity in any jurisdiction where such distribution or use would be
        contrary to law or regulation. Those who choose to access the Services from other locations
        do so on their own initiative and are solely responsible for compliance with local laws.
      </p>
      <p className="mb-6">
        The Services are not tailored to comply with industry-specific regulations (HIPAA, FISMA,
        etc.), so if your interactions would be subject to such laws, you may not use the Services.
      </p>

      {/* 2 */}
      <h2 id="ip" className="text-xl font-bold text-text mt-10 mb-4">
        2. Intellectual Property Rights
      </h2>
      <h3 className="font-semibold text-text mb-2">Our intellectual property</h3>
      <p className="mb-4">
        We are the owner or licensee of all intellectual property rights in our Services, including
        all source code, databases, functionality, software, website designs, text, and graphics
        (collectively, the "Content"), as well as the trademarks, service marks, and logos
        contained therein (the "Marks"). Our Content and Marks are protected by copyright and
        trademark laws in the United States and around the world. The Content and Marks are
        provided through the Services "AS IS" for your personal, non-commercial use only.
      </p>
      <h3 className="font-semibold text-text mb-2">Your use of our Services</h3>
      <p className="mb-4">
        Subject to your compliance with these Legal Terms, we grant you a non-exclusive,
        non-transferable, revocable license to access the Services solely for your personal,
        non-commercial use. No part of the Services, Content, or Marks may be copied, reproduced,
        republished, uploaded, posted, publicly displayed, encoded, translated, transmitted,
        distributed, sold, or licensed for any commercial purpose without our express prior written
        permission.
      </p>
      <p className="mb-4">
        For permissions inquiries, please use the{" "}
        <a href="/app/contact" className="text-brand underline hover:text-brand-dark">contact form</a>.
      </p>
      <p className="mb-4">
        We reserve all rights not expressly granted to you. Any breach of these Intellectual
        Property Rights will constitute a material breach of our Legal Terms and your right to use
        our Services will terminate immediately.
      </p>
      <h3 className="font-semibold text-text mb-2">Your submissions</h3>
      <p className="mb-4">
        By sending us any question, comment, suggestion, idea, or feedback about the Services
        ("Submissions"), you agree to assign to us all intellectual property rights in such
        Submission. You agree that we shall own this Submission and be entitled to its unrestricted
        use for any lawful purpose without acknowledgment or compensation to you.
      </p>
      <p className="mb-6">
        You are solely responsible for your Submissions and you expressly agree to reimburse us
        for any losses we suffer because of your breach of this section, any third party's
        intellectual property rights, or applicable law.
      </p>

      {/* 3 */}
      <h2 id="userreps" className="text-xl font-bold text-text mt-10 mb-4">
        3. User Representations
      </h2>
      <p className="mb-4">By using the Services, you represent and warrant that:</p>
      <ol className="list-decimal pl-6 space-y-2 mb-6">
        <li>all registration information you submit will be true, accurate, current, and complete;</li>
        <li>you will maintain the accuracy of such information and promptly update it as necessary;</li>
        <li>you have the legal capacity and agree to comply with these Legal Terms;</li>
        <li>you are not a minor in the jurisdiction in which you reside;</li>
        <li>you will not access the Services through automated or non-human means;</li>
        <li>you will not use the Services for any illegal or unauthorized purpose; and</li>
        <li>your use of the Services will not violate any applicable law or regulation.</li>
      </ol>
      <p className="mb-6">
        If you provide any information that is untrue, inaccurate, not current, or incomplete, we
        have the right to suspend or terminate your account and refuse any current or future use
        of the Services.
      </p>

      {/* 4 */}
      <h2 id="userreg" className="text-xl font-bold text-text mt-10 mb-4">
        4. User Registration
      </h2>
      <p className="mb-6">
        You may be required to register to use the Services. You agree to keep your credentials
        confidential and will be responsible for all use of your account. We reserve the right to
        remove, reclaim, or change a username you select if we determine it is inappropriate,
        obscene, or otherwise objectionable.
      </p>

      {/* 5 */}
      <h2 id="prohibited" className="text-xl font-bold text-text mt-10 mb-4">
        5. Prohibited Activities
      </h2>
      <p className="mb-4">
        You may not access or use the Services for any purpose other than that for which we make
        the Services available. As a user of the Services, you agree not to:
      </p>
      <ul className="list-disc pl-6 space-y-2 mb-6">
        <li>Systematically retrieve data or content from the Services to create a collection, compilation, or database without written permission from us.</li>
        <li>Trick, defraud, or mislead us and other users, especially to learn sensitive account information.</li>
        <li>Circumvent, disable, or otherwise interfere with security-related features of the Services.</li>
        <li>Use any information obtained from the Services to harass, abuse, or harm another person.</li>
        <li>Use the Services in a manner inconsistent with any applicable laws or regulations.</li>
        <li>Engage in unauthorized framing of or linking to the Services.</li>
        <li>Upload or transmit viruses, Trojan horses, or other material that interferes with any party's use of the Services.</li>
        <li>Engage in any automated use of the system, such as scripts, data mining robots, or similar data gathering tools.</li>
        <li>Attempt to impersonate another user or person or use the username of another user.</li>
        <li>Interfere with, disrupt, or create an undue burden on the Services or connected networks.</li>
        <li>Attempt to bypass any measures designed to prevent or restrict access to the Services.</li>
        <li>Copy or adapt the Services' software, including but not limited to HTML, JavaScript, or other code.</li>
        <li>Decipher, decompile, disassemble, or reverse engineer any software comprising the Services.</li>
        <li>Make any unauthorized use of the Services, including collecting email addresses of users for the purpose of sending unsolicited email.</li>
        <li>Use the Services as part of any effort to compete with us or for any revenue-generating endeavor or commercial enterprise.</li>
      </ul>

      {/* 6 */}
      <h2 id="ugc" className="text-xl font-bold text-text mt-10 mb-4">
        6. User Generated Contributions
      </h2>
      <p className="mb-6">
        The Services do not offer users the ability to submit or post public content.
      </p>

      {/* 7 */}
      <h2 id="license" className="text-xl font-bold text-text mt-10 mb-4">
        7. Contribution License
      </h2>
      <p className="mb-4">
        You and the Services agree that we may access, store, process, and use any information and
        personal data that you provide in accordance with the terms of the Privacy Policy and your
        choices (including settings).
      </p>
      <p className="mb-6">
        By submitting suggestions or other feedback regarding the Services, you agree that we can
        use and share such feedback for any purpose without compensation to you.
      </p>

      {/* 8 */}
      <h2 id="thirdparty" className="text-xl font-bold text-text mt-10 mb-4">
        8. Third-Party Websites and Content
      </h2>
      <p className="mb-6">
        The Services may contain links to other websites ("Third-Party Websites") as well as
        content belonging to or originating from third parties ("Third-Party Content"). Such
        Third-Party Websites and Third-Party Content are not investigated, monitored, or checked
        for accuracy by us, and we are not responsible for any Third-Party Websites accessed
        through the Services. Inclusion of or linking to any Third-Party Websites does not imply
        approval or endorsement by us. If you decide to leave the Services and access Third-Party
        Websites, you do so at your own risk.
      </p>

      {/* 9 */}
      <h2 id="sitemanage" className="text-xl font-bold text-text mt-10 mb-4">
        9. Services Management
      </h2>
      <p className="mb-6">
        We reserve the right, but not the obligation, to: (1) monitor the Services for violations
        of these Legal Terms; (2) take appropriate legal action against anyone who violates the
        law or these Legal Terms; (3) in our sole discretion, refuse, restrict access to, or limit
        the availability of any portion of the Services; and (4) otherwise manage the Services in
        a manner designed to protect our rights and property and to facilitate the proper
        functioning of the Services.
      </p>

      {/* 10 */}
      <h2 id="ppyes" className="text-xl font-bold text-text mt-10 mb-4">
        10. Privacy Policy
      </h2>
      <p className="mb-6">
        We care about data privacy and security. Please review our Privacy Policy at{" "}
        <a href="/privacy" className="text-brand underline hover:text-brand-dark">
          https://sffstock.com/privacy
        </a>
        . By using the Services, you agree to be bound by our Privacy Policy, which is incorporated
        into these Legal Terms. The Services are hosted in the United States. If you access the
        Services from any other region with laws governing personal data collection that differ
        from US laws, your continued use of the Services constitutes consent to have your data
        transferred to and processed in the United States.
      </p>

      {/* 11 */}
      <h2 id="terms" className="text-xl font-bold text-text mt-10 mb-4">
        11. Term and Termination
      </h2>
      <p className="mb-4">
        These Legal Terms shall remain in full force and effect while you use the Services. WE
        RESERVE THE RIGHT TO, IN OUR SOLE DISCRETION AND WITHOUT NOTICE OR LIABILITY, DENY ACCESS
        TO AND USE OF THE SERVICES TO ANY PERSON FOR ANY REASON, INCLUDING FOR BREACH OF ANY
        REPRESENTATION, WARRANTY, OR COVENANT CONTAINED IN THESE LEGAL TERMS OR OF ANY APPLICABLE
        LAW OR REGULATION. WE MAY TERMINATE YOUR USE OR PARTICIPATION IN THE SERVICES OR DELETE
        YOUR ACCOUNT AND ANY INFORMATION THAT YOU POSTED AT ANY TIME, WITHOUT WARNING, IN OUR
        SOLE DISCRETION.
      </p>
      <p className="mb-6">
        If we terminate or suspend your account for any reason, you are prohibited from
        registering and creating a new account under your name, a fake or borrowed name, or the
        name of any third party.
      </p>

      {/* 12 */}
      <h2 id="modifications" className="text-xl font-bold text-text mt-10 mb-4">
        12. Modifications and Interruptions
      </h2>
      <p className="mb-4">
        We reserve the right to change, modify, or remove the contents of the Services at any
        time or for any reason at our sole discretion without notice. We will not be liable to you
        or any third party for any modification, suspension, or discontinuance of the Services.
      </p>
      <p className="mb-6">
        We cannot guarantee the Services will be available at all times. We reserve the right to
        change, revise, update, suspend, discontinue, or otherwise modify the Services at any time
        without notice. We have no liability for any loss, damage, or inconvenience caused by your
        inability to access or use the Services during any downtime or discontinuance.
      </p>

      {/* 13 */}
      <h2 id="law" className="text-xl font-bold text-text mt-10 mb-4">
        13. Governing Law
      </h2>
      <p className="mb-6">
        These Legal Terms and your use of the Services are governed by and construed in accordance
        with the laws of the State of Wisconsin applicable to agreements made and to be entirely
        performed within the State of Wisconsin, without regard to its conflict of law principles.
      </p>

      {/* 14 */}
      <h2 id="disputes" className="text-xl font-bold text-text mt-10 mb-4">
        14. Dispute Resolution
      </h2>
      <h3 className="font-semibold text-text mb-2">Informal Negotiations</h3>
      <p className="mb-4">
        To expedite resolution and control the cost of any dispute, the parties agree to first
        attempt to negotiate any dispute informally for at least 30 days before initiating
        arbitration. Such informal negotiations commence upon written notice from one party to the
        other.
      </p>
      <h3 className="font-semibold text-text mb-2">Binding Arbitration</h3>
      <p className="mb-4">
        Any dispute arising out of or in connection with these Legal Terms shall be referred to
        and finally resolved by binding arbitration. The arbitration shall be conducted by one
        arbitrator in Madison, Wisconsin, in the English language, under the substantive law of
        the State of Wisconsin.
      </p>
      <h3 className="font-semibold text-text mb-2">Restrictions</h3>
      <p className="mb-4">
        The parties agree that any arbitration shall be limited to the dispute between the parties
        individually. No arbitration shall be joined with any other proceeding, and there is no
        right or authority for any dispute to be arbitrated on a class-action basis.
      </p>
      <h3 className="font-semibold text-text mb-2">
        Exceptions to Informal Negotiations and Arbitration
      </h3>
      <p className="mb-6">
        The following disputes are not subject to the above provisions: (a) any disputes seeking
        to enforce or protect intellectual property rights; (b) any dispute related to allegations
        of theft, piracy, invasion of privacy, or unauthorized use; and (c) any claim for
        injunctive relief.
      </p>

      {/* 15 */}
      <h2 id="corrections" className="text-xl font-bold text-text mt-10 mb-4">
        15. Corrections
      </h2>
      <p className="mb-6">
        There may be information on the Services that contains typographical errors, inaccuracies,
        or omissions. We reserve the right to correct any errors, inaccuracies, or omissions and
        to change or update the information on the Services at any time without prior notice.
      </p>

      {/* 16 */}
      <h2 id="disclaimer" className="text-xl font-bold text-text mt-10 mb-4">
        16. Disclaimer
      </h2>
      <p className="mb-6">
        THE SERVICES ARE PROVIDED ON AN AS-IS AND AS-AVAILABLE BASIS. YOU AGREE THAT YOUR USE OF
        THE SERVICES WILL BE AT YOUR SOLE RISK. TO THE FULLEST EXTENT PERMITTED BY LAW, WE
        DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING THE IMPLIED WARRANTIES OF
        MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE MAKE NO
        WARRANTIES OR REPRESENTATIONS ABOUT THE ACCURACY OR COMPLETENESS OF THE SERVICES'
        CONTENT. IN PARTICULAR, WE DO NOT GUARANTEE THAT STOCK ALERTS WILL BE DELIVERED IN A
        TIMELY MANNER, THAT ALL STOCK CHANGES WILL BE DETECTED, OR THAT ITEMS WILL REMAIN
        AVAILABLE FOR PURCHASE AFTER AN ALERT IS SENT. WE WILL ASSUME NO LIABILITY OR
        RESPONSIBILITY FOR ANY ERRORS, MISTAKES, OR INACCURACIES OF CONTENT AND MATERIALS, ANY
        INTERRUPTION OR CESSATION OF TRANSMISSION TO OR FROM THE SERVICES, OR ANY BUGS, VIRUSES,
        OR TROJAN HORSES TRANSMITTED TO OR THROUGH THE SERVICES BY ANY THIRD PARTY.
      </p>

      {/* 17 */}
      <h2 id="liability" className="text-xl font-bold text-text mt-10 mb-4">
        17. Limitations of Liability
      </h2>
      <p className="mb-6">
        IN NO EVENT WILL WE OR OUR DIRECTORS, EMPLOYEES, OR AGENTS BE LIABLE TO YOU OR ANY THIRD
        PARTY FOR ANY DIRECT, INDIRECT, CONSEQUENTIAL, EXEMPLARY, INCIDENTAL, SPECIAL, OR
        PUNITIVE DAMAGES, INCLUDING LOST PROFIT, LOST REVENUE, LOSS OF DATA, OR OTHER DAMAGES
        ARISING FROM YOUR USE OF THE SERVICES, EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF
        SUCH DAMAGES.
      </p>

      {/* 18 */}
      <h2 id="indemnification" className="text-xl font-bold text-text mt-10 mb-4">
        18. Indemnification
      </h2>
      <p className="mb-6">
        You agree to defend, indemnify, and hold us harmless, including our respective officers,
        agents, partners, and employees, from and against any loss, damage, liability, claim, or
        demand, including reasonable attorneys' fees and expenses, made by any third party due to
        or arising out of: (1) use of the Services; (2) breach of these Legal Terms; (3) any
        breach of your representations and warranties set forth in these Legal Terms; (4) your
        violation of the rights of a third party, including but not limited to intellectual
        property rights; or (5) any overt harmful act toward any other user of the Services.
      </p>

      {/* 19 */}
      <h2 id="userdata" className="text-xl font-bold text-text mt-10 mb-4">
        19. User Data
      </h2>
      <p className="mb-6">
        We will maintain certain data that you transmit to the Services for the purpose of
        managing the performance of the Services. Although we perform regular routine backups of
        data, you are solely responsible for all data that you transmit or that relates to any
        activity you have undertaken using the Services. You agree that we shall have no liability
        to you for any loss or corruption of any such data, and you hereby waive any right of
        action against us arising from any such loss or corruption.
      </p>

      {/* 20 */}
      <h2 id="electronic" className="text-xl font-bold text-text mt-10 mb-4">
        20. Electronic Communications, Transactions, and Signatures
      </h2>
      <p className="mb-6">
        Visiting the Services, sending us emails, and completing online forms constitute electronic
        communications. You consent to receive electronic communications, and you agree that all
        agreements, notices, disclosures, and other communications we provide to you
        electronically satisfy any legal requirement that such communication be in writing. YOU
        HEREBY AGREE TO THE USE OF ELECTRONIC SIGNATURES, CONTRACTS, ORDERS, AND OTHER RECORDS,
        AND TO ELECTRONIC DELIVERY OF NOTICES, POLICIES, AND RECORDS OF TRANSACTIONS INITIATED OR
        COMPLETED BY US OR VIA THE SERVICES.
      </p>

      {/* 21 */}
      <h2 id="california" className="text-xl font-bold text-text mt-10 mb-4">
        21. California Users and Residents
      </h2>
      <p className="mb-6">
        If any complaint with us is not satisfactorily resolved, you can contact the Complaint
        Assistance Unit of the Division of Consumer Services of the California Department of
        Consumer Affairs in writing at 1625 North Market Blvd., Suite N 112, Sacramento,
        California 95834 or by telephone at (800) 952-5210 or (916) 445-1254.
      </p>

      {/* 22 */}
      <h2 id="misc" className="text-xl font-bold text-text mt-10 mb-4">
        22. Miscellaneous
      </h2>
      <p className="mb-6">
        These Legal Terms and any policies or operating rules posted by us on the Services
        constitute the entire agreement and understanding between you and us. Our failure to
        exercise or enforce any right or provision of these Legal Terms shall not operate as a
        waiver of such right or provision. These Legal Terms operate to the fullest extent
        permissible by law. If any provision of these Legal Terms is determined to be unlawful,
        void, or unenforceable, that provision is deemed severable and does not affect the
        validity and enforceability of any remaining provisions. There is no joint venture,
        partnership, employment, or agency relationship created between you and us as a result of
        these Legal Terms or use of the Services.
      </p>

      {/* 23 */}
      <h2 id="contact" className="text-xl font-bold text-text mt-10 mb-4">
        23. Contact Us
      </h2>
      <p className="mb-6">
        In order to resolve a complaint regarding the Services or to receive further information
        regarding use of the Services, please contact us via the{" "}
        <a href="/app/contact" className="text-brand underline hover:text-brand-dark">contact form</a>{" "}
        (login required) or email us at{" "}
        <a href="mailto:sf.stock.updates@gmail.com" className="text-brand underline hover:text-brand-dark">
          sf.stock.updates@gmail.com
        </a>
      </p>

      <p className="mt-12 text-xs text-text-muted">
        These Terms of Service were generated with assistance from{" "}
        <a
          href="https://termly.io/products/terms-and-conditions-generator/"
          className="text-brand underline hover:text-brand-dark"
          target="_blank"
          rel="noopener noreferrer"
        >
          Termly's Terms and Conditions Generator
        </a>
        .
      </p>
    </div>
  )
}

export default function Terms() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-alt">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
      </div>
    )
  }

  if (user) {
    return (
      <Layout>
        <TermsContent embedded />
      </Layout>
    )
  }

  return (
    <div className="min-h-screen bg-surface-alt">
      <TermsContent />
    </div>
  )
}
