export default function Privacy() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-12 text-sm text-gray-700 leading-relaxed">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
      <p className="text-gray-500 mb-10">Last updated March 30, 2026</p>

      <p className="mb-6">
        This Privacy Notice for SFF Stock Alerts ("we," "us," or "our") describes how and why we
        might access, collect, store, use, and/or share ("process") your personal information when
        you use our services ("Services"), including when you visit our website at{" "}
        <a href="https://sffstock.com" className="text-blue-600 underline">
          https://sffstock.com
        </a>{" "}
        or engage with us in other related ways.
      </p>

      <p className="mb-10">
        <strong>Questions or concerns?</strong> Reading this Privacy Notice will help you understand
        your privacy rights and choices. If you do not agree with our policies and practices, please
        do not use our Services. If you have questions, please contact us via the{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact form
        </a>
        .
      </p>

      {/* Summary */}
      <h2 className="text-xl font-bold text-gray-900 mt-10 mb-4">Summary of Key Points</h2>
      <ul className="list-disc pl-6 space-y-3 mb-10">
        <li>
          <strong>What personal information do we process?</strong> We collect your email address
          and notification preferences when you register.
        </li>
        <li>
          <strong>Do we process sensitive personal information?</strong> No.
        </li>
        <li>
          <strong>Do we collect information from third parties?</strong> No.
        </li>
        <li>
          <strong>How do we process your information?</strong> To provide stock alert notifications
          and manage your account.
        </li>
        <li>
          <strong>With whom do we share your information?</strong> We use Supabase for data storage
          and authentication, and AWS for email delivery. We do not sell your data.
        </li>
        <li>
          <strong>How do we keep your information safe?</strong> We use industry-standard technical
          measures, though no method of transmission is 100% secure.
        </li>
        <li>
          <strong>How do you exercise your rights?</strong> Visit our{" "}
          <a href="/app/contact" className="text-blue-600 underline">
            contact page
          </a>{" "}
          or manage preferences in your account settings.
        </li>
      </ul>

      {/* TOC */}
      <h2 className="text-xl font-bold text-gray-900 mt-10 mb-4">Table of Contents</h2>
      <ol className="list-decimal pl-6 space-y-1 mb-10">
        <li><a href="#infocollect" className="text-blue-600 underline">What Information Do We Collect?</a></li>
        <li><a href="#infouse" className="text-blue-600 underline">How Do We Process Your Information?</a></li>
        <li><a href="#legalbases" className="text-blue-600 underline">What Legal Bases Do We Rely On?</a></li>
        <li><a href="#whoshare" className="text-blue-600 underline">When and With Whom Do We Share Your Information?</a></li>
        <li><a href="#cookies" className="text-blue-600 underline">Do We Use Cookies and Other Tracking Technologies?</a></li>
        <li><a href="#inforetain" className="text-blue-600 underline">How Long Do We Keep Your Information?</a></li>
        <li><a href="#infosafe" className="text-blue-600 underline">How Do We Keep Your Information Safe?</a></li>
        <li><a href="#infominors" className="text-blue-600 underline">Do We Collect Information From Minors?</a></li>
        <li><a href="#privacyrights" className="text-blue-600 underline">What Are Your Privacy Rights?</a></li>
        <li><a href="#DNT" className="text-blue-600 underline">Controls for Do-Not-Track Features</a></li>
        <li><a href="#uslaws" className="text-blue-600 underline">Do United States Residents Have Specific Privacy Rights?</a></li>
        <li><a href="#policyupdates" className="text-blue-600 underline">Do We Make Updates to This Notice?</a></li>
        <li><a href="#contact" className="text-blue-600 underline">How Can You Contact Us About This Notice?</a></li>
        <li><a href="#request" className="text-blue-600 underline">How Can You Review, Update, or Delete Your Data?</a></li>
      </ol>

      {/* Section 1 */}
      <h2 id="infocollect" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        1. What Information Do We Collect?
      </h2>
      <h3 className="font-semibold text-gray-900 mb-2">Personal information you disclose to us</h3>
      <p className="mb-4">
        We collect personal information that you voluntarily provide when you register on the
        Services or otherwise contact us. This includes:
      </p>
      <ul className="list-disc pl-6 space-y-1 mb-6">
        <li>Email addresses</li>
        <li>Notification preferences (per-store alert settings)</li>
      </ul>
      <p className="mb-6">
        We do not process sensitive personal information.
      </p>

      <h3 className="font-semibold text-gray-900 mb-2">Information automatically collected</h3>
      <p className="mb-4">
        Some information is collected automatically when you visit our Services, such as your IP
        address and browser characteristics. This information is used to maintain security and
        operation of the Services. It does not reveal your specific identity.
      </p>
      <p className="mb-4">
        We also collect information through cookies and similar technologies. The information we
        collect includes:
      </p>
      <ul className="list-disc pl-6 space-y-2 mb-6">
        <li>
          <em>Log and Usage Data.</em> Service-related diagnostic information including IP address,
          device information, browser type, and activity timestamps.
        </li>
        <li>
          <em>Device Data.</em> Information about your device including browser type, operating
          system, and system configuration.
        </li>
      </ul>

      {/* Section 2 */}
      <h2 id="infouse" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        2. How Do We Process Your Information?
      </h2>
      <p className="mb-4">
        We process your personal information for the following purposes:
      </p>
      <ul className="list-disc pl-6 space-y-2 mb-6">
        <li>
          <strong>To facilitate account creation and authentication.</strong> We process your
          information so you can create and log in to your account.
        </li>
        <li>
          <strong>To deliver services to the user.</strong> We use your email and preferences to
          send stock alert notifications for the stores you have subscribed to.
        </li>
        <li>
          <strong>To respond to user inquiries and offer support.</strong> We may process your
          information to respond to your questions and resolve issues.
        </li>
        <li>
          <strong>To identify usage trends.</strong> We may analyze how our Services are used to
          improve them.
        </li>
      </ul>

      {/* Section 3 */}
      <h2 id="legalbases" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        3. What Legal Bases Do We Rely On?
      </h2>
      <p className="mb-4">
        <strong>
          <em>If you are located in the EU or UK, this section applies to you.</em>
        </strong>
      </p>
      <p className="mb-4">
        The GDPR and UK GDPR require us to explain the valid legal bases we rely on to process your
        personal information:
      </p>
      <ul className="list-disc pl-6 space-y-2 mb-6">
        <li>
          <strong>Consent.</strong> You have given us permission to use your personal information
          for a specific purpose (receiving stock alerts). You can withdraw consent at any time via
          your account preferences or by contacting us.
        </li>
        <li>
          <strong>Performance of a Contract.</strong> We process your information to fulfill our
          service obligations to you.
        </li>
        <li>
          <strong>Legal Obligations.</strong> We may process your information where required by
          law.
        </li>
      </ul>
      <p className="mb-6">
        <strong>
          <em>If you are located in Canada, this section applies to you.</em>
        </strong>{" "}
        We may process your information if you have given us express or implied consent. You can
        withdraw consent at any time.
      </p>

      {/* Section 4 */}
      <h2 id="whoshare" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        4. When and With Whom Do We Share Your Personal Information?
      </h2>
      <p className="mb-4">
        We use the following third-party service providers to operate the Services:
      </p>
      <ul className="list-disc pl-6 space-y-2 mb-6">
        <li>
          <strong>Supabase</strong> — database and authentication provider. Your email address and
          preferences are stored in Supabase.
        </li>
        <li>
          <strong>Amazon Web Services (AWS SES)</strong> — email delivery provider used to send
          stock notifications.
        </li>
        <li>
          <strong>Vercel</strong> — frontend hosting provider.
        </li>
      </ul>
      <p className="mb-6">
        We may also share or transfer your information in connection with a merger, sale, or
        acquisition of all or a portion of our business. We do not sell your personal information
        to third parties.
      </p>

      {/* Section 5 */}
      <h2 id="cookies" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        5. Do We Use Cookies and Other Tracking Technologies?
      </h2>
      <p className="mb-6">
        We use cookies and similar tracking technologies to maintain the security of our Services
        and your account, and to support basic site functions including authentication sessions
        managed by Supabase. We do not use cookies for advertising or cross-site tracking.
      </p>

      {/* Section 6 */}
      <h2 id="inforetain" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        6. How Long Do We Keep Your Information?
      </h2>
      <p className="mb-6">
        We keep your personal information for as long as you have an active account with us. When
        your account is deactivated or deleted, we will delete or anonymize your personal
        information. Email delivery logs may be retained in anonymized form for operational
        purposes.
      </p>

      {/* Section 7 */}
      <h2 id="infosafe" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        7. How Do We Keep Your Information Safe?
      </h2>
      <p className="mb-6">
        We implement appropriate technical and organizational security measures to protect your
        personal information. However, no electronic transmission over the internet can be
        guaranteed to be 100% secure. You should only access the Services within a secure
        environment.
      </p>

      {/* Section 8 */}
      <h2 id="infominors" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        8. Do We Collect Information From Minors?
      </h2>
      <p className="mb-6">
        We do not knowingly collect data from or market to children under 18 years of age. By using
        the Services, you represent that you are at least 18. If you become aware of any data we
        may have collected from a minor, please contact us via the{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact form
        </a>
        .
      </p>

      {/* Section 9 */}
      <h2 id="privacyrights" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        9. What Are Your Privacy Rights?
      </h2>
      <p className="mb-4">
        Depending on your location, you may have rights under applicable data protection laws,
        including the right to:
      </p>
      <ul className="list-disc pl-6 space-y-1 mb-6">
        <li>Access and obtain a copy of your personal information</li>
        <li>Request correction or deletion of your personal information</li>
        <li>Restrict or object to the processing of your personal information</li>
        <li>Withdraw consent at any time</li>
        <li>Data portability (where applicable)</li>
      </ul>
      <p className="mb-4">
        You can manage your notification preferences and deactivate your account at any time via
        your{" "}
        <a href="/app/preferences" className="text-blue-600 underline">
          account preferences page
        </a>
        . For other requests, contact us via the{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact form
        </a>
        .
      </p>
      <p className="mb-4">
        If you are in the EEA or UK and believe we are unlawfully processing your personal
        information, you have the right to complain to your{" "}
        <a
          href="https://ec.europa.eu/justice/data-protection/bodies/authorities/index_en.htm"
          className="text-blue-600 underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          Member State data protection authority
        </a>{" "}
        or the{" "}
        <a
          href="https://ico.org.uk/make-a-complaint/data-protection-complaints/data-protection-complaints/"
          className="text-blue-600 underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          UK data protection authority
        </a>
        .
      </p>
      <p className="mb-6">
        If you are in Switzerland, you may contact the{" "}
        <a
          href="https://www.edoeb.admin.ch/edoeb/en/home.html"
          className="text-blue-600 underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          Federal Data Protection and Information Commissioner
        </a>
        .
      </p>

      {/* Section 10 */}
      <h2 id="DNT" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        10. Controls for Do-Not-Track Features
      </h2>
      <p className="mb-6">
        Most web browsers include a Do-Not-Track ("DNT") feature. No uniform standard for
        recognizing DNT signals has been finalized, and we do not currently respond to DNT signals.
        California law requires us to make this disclosure.
      </p>

      {/* Section 11 */}
      <h2 id="uslaws" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        11. Do United States Residents Have Specific Privacy Rights?
      </h2>
      <p className="mb-4">
        Residents of certain US states may have additional rights regarding their personal
        information. The table below shows the categories of personal information we have collected
        in the past twelve months.
      </p>

      <div className="overflow-x-auto mb-6">
        <table className="w-full border-collapse border border-gray-300 text-sm">
          <thead>
            <tr className="bg-gray-50">
              <th className="border border-gray-300 px-3 py-2 text-left font-semibold">Category</th>
              <th className="border border-gray-300 px-3 py-2 text-left font-semibold">Examples</th>
              <th className="border border-gray-300 px-3 py-2 text-left font-semibold">Collected</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="border border-gray-300 px-3 py-2">A. Identifiers</td>
              <td className="border border-gray-300 px-3 py-2">Email address, online identifier, IP address</td>
              <td className="border border-gray-300 px-3 py-2">YES</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">B. California Customer Records</td>
              <td className="border border-gray-300 px-3 py-2">Name, contact information, financial information</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">C. Protected classification characteristics</td>
              <td className="border border-gray-300 px-3 py-2">Gender, age, race, ethnicity</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">D. Commercial information</td>
              <td className="border border-gray-300 px-3 py-2">Purchase history, financial details</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">E. Biometric information</td>
              <td className="border border-gray-300 px-3 py-2">Fingerprints, voiceprints</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">F. Internet or network activity</td>
              <td className="border border-gray-300 px-3 py-2">Browsing history, interactions with our site</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">G. Geolocation data</td>
              <td className="border border-gray-300 px-3 py-2">
                IP-derived approximate location only (no precise device location collected)
              </td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">H. Audio, electronic, sensory information</td>
              <td className="border border-gray-300 px-3 py-2">Images, audio, video recordings</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">I. Professional or employment information</td>
              <td className="border border-gray-300 px-3 py-2">Job title, work history</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">J. Education information</td>
              <td className="border border-gray-300 px-3 py-2">Student records</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">K. Inferences from personal information</td>
              <td className="border border-gray-300 px-3 py-2">Profiles of preferences or characteristics</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
            <tr>
              <td className="border border-gray-300 px-3 py-2">L. Sensitive personal information</td>
              <td className="border border-gray-300 px-3 py-2">—</td>
              <td className="border border-gray-300 px-3 py-2">NO</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="mb-4">
        We will use and retain Category A personal information for as long as you have an active
        account with us.
      </p>
      <p className="mb-4">
        We have not disclosed, sold, or shared any personal information to third parties for a
        business or commercial purpose in the preceding twelve months, and will not do so in the
        future.
      </p>

      <h3 className="font-semibold text-gray-900 mt-6 mb-2">Your Rights</h3>
      <p className="mb-4">
        Depending on your state of residence, you may have the right to:
      </p>
      <ul className="list-disc pl-6 space-y-1 mb-6">
        <li>Know whether we are processing your personal data</li>
        <li>Access your personal data</li>
        <li>Correct inaccuracies in your personal data</li>
        <li>Request deletion of your personal data</li>
        <li>Obtain a copy of the personal data you previously shared with us</li>
        <li>Non-discrimination for exercising your rights</li>
        <li>Opt out of the processing of your personal data for targeted advertising or sale</li>
      </ul>

      <h3 className="font-semibold text-gray-900 mt-6 mb-2">How to Exercise Your Rights</h3>
      <p className="mb-6">
        To exercise these rights, please visit our{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact page
        </a>{" "}
        or manage your preferences directly in your account settings.
      </p>

      {/* Section 12 */}
      <h2 id="policyupdates" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        12. Do We Make Updates to This Notice?
      </h2>
      <p className="mb-6">
        Yes, we will update this notice as necessary to stay compliant with relevant laws. The
        updated version will be indicated by an updated date at the top of this page. We encourage
        you to review this Privacy Notice periodically.
      </p>

      {/* Section 13 */}
      <h2 id="contact" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        13. How Can You Contact Us About This Notice?
      </h2>
      <p className="mb-6">
        If you have questions or comments about this notice, please contact us via the{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact form
        </a>{" "}
        on our website.
      </p>

      {/* Section 14 */}
      <h2 id="request" className="text-xl font-bold text-gray-900 mt-10 mb-4">
        14. How Can You Review, Update, or Delete Your Data?
      </h2>
      <p className="mb-6">
        You have the right to request access to, correction of, or deletion of your personal
        information. You can manage your notification preferences and deactivate your account at
        any time via your{" "}
        <a href="/app/preferences" className="text-blue-600 underline">
          account preferences page
        </a>
        . For data deletion or export requests, please use the{" "}
        <a href="/app/contact" className="text-blue-600 underline">
          contact form
        </a>
        .
      </p>

      <p className="mt-12 text-xs text-gray-400">
        This Privacy Policy was generated with assistance from{" "}
        <a
          href="https://termly.io/products/privacy-policy-generator/"
          className="underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          Termly's Privacy Policy Generator
        </a>
        .
      </p>
    </div>
  );
}
