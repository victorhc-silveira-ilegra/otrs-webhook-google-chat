package Kernel::System::Ticket::Event::GoogleChatAlert;

use strict;
use warnings;

sub new {
    my ( $Type, %Param ) = @_;
    my $Self = {};
    for my $Key ( keys %Param ) {
        $Self->{$Key} = $Param{$Key};
    }
    return bless $Self, $Type;
}

sub Run {
    my ( $Self, %Param ) = @_;

    return 1 if !$Param{Data}->{TicketID};

    my %Ticket = $Self->{TicketObject}->TicketGet(
        TicketID => $Param{Data}->{TicketID},
        UserID   => 1,
    );

    return 1 if !%Ticket;

    my $ConfiguredQueue = $Param{Config}->{Queue} // '';
    if ( $ConfiguredQueue ne '' ) {
        my $TicketQueue = $Ticket{Queue} // '';
        return 1 if $TicketQueue ne $ConfiguredQueue;
    }

    my $Bin = $ENV{NOTIFIER_BIN} || '/opt/notifier/bin/otrs-gchat-alert';
    my @Cmd = (
        $Bin,
        '--ticket-id',     $Ticket{TicketID},
        '--ticket-number', $Ticket{TicketNumber},
        '--title',         $Ticket{Title} // '',
        '--queue',         $Ticket{Queue} // '',
    );

    system(@Cmd);
    if ( $? != 0 ) {
        $Self->{LogObject}->Log(
            Priority => 'error',
            Message  => "GoogleChatAlert failed for TicketID=$Ticket{TicketID} status=$?",
        );
    }

    return 1;
}

1;
