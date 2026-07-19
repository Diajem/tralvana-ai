export interface AffiliateProgramme {
  id: string;
  partner: string;
  name: string;
  vertical: string;
  disclosure_text: string;
  destination_url: string;
}

export interface OutboundLink {
  click_id: string;
  redirect_path: string;
  disclosure_text: string;
}
